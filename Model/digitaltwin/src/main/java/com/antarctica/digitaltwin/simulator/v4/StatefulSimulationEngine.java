package com.antarctica.digitaltwin.simulator.v4;

import java.time.*;
import java.util.*;

/**
 * V4 causal daily engine. Randomness is keyed by seed+day, which makes a run
 * replayable and prevents an API restart from changing an already planned day.
 */
public final class StatefulSimulationEngine {
    private final SimulationConfig c;
    public StatefulSimulationEngine(SimulationConfig config) { this.c=config; }
    public SimulationSnapshot step(StationState s) {
        Random r = new Random(s.seed + 31_415_927L*s.dayIndex); s.events.clear();
        weather(s,r); population(s,r); mission(s,r); logistics(s,r);
        double load=powerDemand(s), solar=solar(s), wind=wind(s), renewable=solar+wind;
        double net=load-renewable, batteryPower=battery(s,net);
        double generatorOutput=dispatch(s,Math.max(0,net-batteryPower),r);
        double fuel=fuel(s,generatorOutput); inventory(s,load,r); maintenance(s,r); validate(s);
        SimulationSnapshot out = new SimulationSnapshot(s.date,s.stationId,s.temperatureC,s.windSpeedKmh,solar,wind,
            load,generatorOutput,s.generatorRuntimeHours,s.fuelStockLitres,fuel,s.batterySocPercent,s.crew+s.scientists,
            s.mission,s.inventory.get("food_days"),s.inventory.get("medical_kits"),s.inventory.get("critical_spares"),
            s.generatorHealthPercent,meanHealth(s),s.stormDaysRemaining>0,s.generatorFailed,List.copyOf(s.events));
        s.date=s.date.plusDays(1); s.dayIndex++; return out;
    }
    private void weather(StationState s, Random r) {
        int doy=s.date.getDayOfYear(); double seasonal=-17-15*Math.cos(2*Math.PI*(doy-15)/365.25);
        s.temperatureC=.82*s.temperatureC+.18*seasonal+r.nextGaussian()*1.7;
        boolean storm=s.stormDaysRemaining>0 || r.nextDouble()<(.025+Math.max(0,-s.temperatureC-22)*.002);
        if(storm){ s.stormDaysRemaining=Math.max(0,s.stormDaysRemaining-1); if(s.stormDaysRemaining==0 && r.nextDouble()<.55) s.stormDaysRemaining=1+r.nextInt(3); }
        s.windSpeedKmh=Math.max(0,.72*s.windSpeedKmh+.28*(storm?65:18)+r.nextGaussian()*5);
        s.windDirectionDeg=(s.windDirectionDeg+r.nextGaussian()*18+360)%360; s.cloudCoverPercent=Math.min(100,Math.max(0,.7*s.cloudCoverPercent+.3*(storm?88:42)+r.nextGaussian()*9));
        s.humidityPercent=Math.min(100,Math.max(25,.8*s.humidityPercent+.2*(storm?88:63)+r.nextGaussian()*4));
        s.snowfallCm=storm?Math.max(0,r.nextGaussian()*1.2+2.0):0; s.snowDepthCm=Math.max(0,s.snowDepthCm*.996+s.snowfallCm);
        s.visibilityM=storm?Math.max(100,3000-s.windSpeedKmh*25):Math.max(2000,12000-s.cloudCoverPercent*35);
        double dayLength=polarDaylightHours(doy); s.solarRadiationWm2=Math.max(0,760*Math.sin(Math.PI*dayLength/24)*(1-s.cloudCoverPercent/120));
        if(storm) s.events.add("WEATHER_STORM");
    }
    private void population(StationState s, Random r) {
        boolean summer=isSummer(s.date); int target=summer?c.summerPopulation:c.winterPopulation;
        int total=s.crew+s.scientists; if(total<target && (s.date.getDayOfMonth()==1 || r.nextDouble()<.015)){ s.scientists+=Math.min(5,target-total); s.events.add("CREW_ROTATION_ARRIVAL"); }
        if(total>target && (s.date.getDayOfMonth()==1 || r.nextDouble()<.012)){ s.scientists=Math.max(2,s.scientists-3); s.events.add("CREW_ROTATION_DEPARTURE"); }
    }
    private void mission(StationState s, Random r) {
        if(s.missionDaysRemaining>0){s.missionDaysRemaining--; if(s.missionDaysRemaining==0)s.mission="NONE"; return;}
        if(isSummer(s.date)&&s.stormDaysRemaining==0&&r.nextDouble()<.10){String[] a={"ICE_CORING","FIELD_SURVEY","SAMPLE_COLLECTION","INSTRUMENT_DEPLOYMENT"};s.mission=a[r.nextInt(a.length)];s.missionDaysRemaining=2+r.nextInt(5);s.events.add("MISSION_"+s.mission);}
    }
    private void logistics(StationState s, Random r) {
        if(s.shipmentEtaDays>0){s.shipmentEtaDays+=(s.stormDaysRemaining>0?1:0); if(s.stormDaysRemaining==0)s.shipmentEtaDays--;}
        if(s.shipmentEtaDays==0){s.fuelStockLitres=Math.min(c.fuelTankLitres,s.fuelStockLitres+65_000); s.inventory.merge("food_days",160d,Double::sum);s.inventory.merge("medical_kits",25d,Double::sum);s.inventory.merge("critical_spares",20d,Double::sum);s.shipmentEtaDays=-1;s.events.add("SHIPMENT_ARRIVED");}
        if(s.shipmentEtaDays<0 && isSummer(s.date) && (s.fuelStockLitres<c.fuelTankLitres*.45 || r.nextDouble()<.004)){s.shipmentEtaDays=12+r.nextInt(22);s.events.add("SHIPMENT_DISPATCHED");}
    }
    private double powerDemand(StationState s) { double people=s.crew+s.scientists; double heating=Math.max(0,-s.temperatureC-5)*3.2*(1+s.windSpeedKmh/180); double mission=s.mission.equals("NONE")?0:35; double lighting=polarDaylightHours(s.date.getDayOfYear())<4?22:5; return 55+people*1.15+heating+mission+lighting+(s.stormDaysRemaining>0?8:0); }
    private double solar(StationState s) { return Math.min(c.solarCapacityKw,c.solarCapacityKw*(s.solarRadiationWm2/750)); }
    private double wind(StationState s) { double v=s.windSpeedKmh; return v<12?0:Math.min(c.windCapacityKw,c.windCapacityKw*Math.pow(Math.min(v,65)/65,3)); }
    private double battery(StationState s,double net) {
        if(net <= 0) {
            double charge=Math.min(-net, 90);
            s.batterySocPercent=Math.min(100,s.batterySocPercent+charge*24*.88/c.batteryCapacityKwh*100);
            return 0;
        }
        double avail=c.batteryCapacityKwh*s.batterySocPercent/100*.90;
        double discharge=Math.min(net,Math.min(90,avail/24));
        s.batterySocPercent=Math.max(0,s.batterySocPercent-discharge*24/c.batteryCapacityKwh*100);
        return discharge;
    }
    private double dispatch(StationState s,double need,Random r) {
        if(need<1)return 0;
        if(s.generatorFailed){s.events.add("GENERATOR_FAILURE_ACTIVE");return 0;}
        if(s.fuelStockLitres<=0){s.events.add("FUEL_DEPLETED");return 0;}
        if(r.nextDouble()<.0008*(1+(100-s.generatorHealthPercent)/20)){s.generatorFailed=true;s.events.add("GENERATOR_FAILURE");return 0;}
        double requested=Math.min(c.generatorCapacityKw,need+Math.max(0,55-need));
        double output=Math.min(requested, outputSupportedByFuel(s.fuelStockLitres, requested));
        if(output < requested) s.events.add("FUEL_CONSTRAINED_GENERATION");
        s.generatorRuntimeHours+=24*output/c.generatorCapacityKw;
        s.generatorRuntimeSinceMaintenanceHours+=24*output/c.generatorCapacityKw;
        if(output>need){double charge=Math.min(output-need,50);s.batterySocPercent=Math.min(100,s.batterySocPercent+charge*24*.88/c.batteryCapacityKwh*100);}
        return output;
    }
    private double outputSupportedByFuel(double available, double requested) {
        if(fuelForOutput(requested)<=available) return requested;
        double low=0, high=requested;
        for(int i=0;i<48;i++){double mid=(low+high)/2; if(fuelForOutput(mid)<=available)low=mid;else high=mid;}
        return low;
    }
    private double fuelForOutput(double output) { return output<=0?0:24*(.19+.00018*output)*output; }
    private double fuel(StationState s,double output) { double used=fuelForOutput(output); s.fuelStockLitres=Math.max(0,s.fuelStockLitres-used); if(s.fuelStockLitres<c.fuelTankLitres*.12)s.events.add("FUEL_LOW");return used; }
    private void inventory(StationState s,double load,Random r) { double people=s.crew+s.scientists; double m=s.mission.equals("NONE")?0:1; s.inventory.compute("food_days",(k,v)->Math.max(0,v-people/Math.max(people,1))); s.inventory.compute("medical_kits",(k,v)->Math.max(0,v-(s.stormDaysRemaining>0?.03:.005))); s.inventory.compute("critical_spares",(k,v)->Math.max(0,v-(s.generatorFailed?1:.01))); s.inventory.compute("research_consumables",(k,v)->Math.max(0,v-m*.8)); }
    private void maintenance(StationState s,Random r) { s.generatorHealthPercent=Math.max(0,s.generatorHealthPercent-.004-s.stormDaysRemaining*.004); for(var e:s.equipmentHealth.entrySet())e.setValue(Math.max(0,e.getValue()-.003-s.stormDaysRemaining*.002)); if(s.generatorRuntimeSinceMaintenanceHours>c.maintenanceIntervalRuntimeHours){s.generatorRuntimeSinceMaintenanceHours=0;s.generatorHealthPercent=Math.min(100,s.generatorHealthPercent+12);s.events.add("SCHEDULED_GENERATOR_MAINTENANCE");} if(s.generatorFailed&&r.nextDouble()<.16&&s.inventory.get("critical_spares")>0){s.generatorFailed=false;s.inventory.compute("critical_spares",(k,v)->v-1);s.generatorHealthPercent=Math.max(65,s.generatorHealthPercent);s.events.add("GENERATOR_REPAIRED");} }
    private void validate(StationState s) { s.fuelStockLitres=Math.max(0,Math.min(c.fuelTankLitres,s.fuelStockLitres));s.batterySocPercent=Math.max(0,Math.min(100,s.batterySocPercent));if(s.crew<0||s.scientists<0)throw new IllegalStateException("Negative population"); for(double v:s.inventory.values())if(v<0)throw new IllegalStateException("Negative inventory"); }
    private boolean isSummer(LocalDate d){int m=d.getMonthValue();return m>=11||m<=3;} private double polarDaylightHours(int doy){return Math.max(0,Math.min(24,12+12*Math.sin(2*Math.PI*(doy-355)/365.25)));} private double meanHealth(StationState s){return s.equipmentHealth.values().stream().mapToDouble(Double::doubleValue).average().orElse(0);}
}
