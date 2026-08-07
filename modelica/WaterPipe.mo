model WaterPipe "Ustálené proudění vody v rovné kruhové trubce"
  parameter Real pressureDrop(unit="Pa", min=1) = 100000;
  parameter Real pipeLength(unit="m", min=0.001) = 10;
  parameter Real diameter(unit="m", min=0.0001) = 0.025;
  parameter Real roughness(unit="m", min=0) = 0.0000015;
  parameter Real temperatureC(unit="degC", min=0.01, max=95) = 20;
  output Real volumeFlow(unit="m3/s", min=0, start=0.001);
  output Real massFlow(unit="kg/s");
  output Real velocity(unit="m/s", min=0, start=1);
  output Real reynolds(min=0, start=10000);
  output Real frictionFactor(min=0, start=0.03);
  output Real rho(unit="kg/m3");
  output Real mu(unit="Pa.s");
protected
  constant Real pi = 3.141592653589793;
  Real area(unit="m2");
equation
  rho = 1000 * (1 - ((temperatureC + 288.9414) /
    (508929.2 * (temperatureC + 68.12963))) * (temperatureC - 3.9863)^2);
  mu = 0.00002414 * 10^(247.8 / (temperatureC + 133.15));
  area = pi * diameter^2 / 4;
  volumeFlow = velocity * area;
  massFlow = rho * volumeFlow;
  reynolds = rho * velocity * diameter / mu;
  frictionFactor = if reynolds < 2300 then 64 / max(reynolds, 1e-6)
    else 0.25 / (log10(roughness / (3.7 * diameter) +
      5.74 / reynolds^0.9))^2;
  pressureDrop = frictionFactor * pipeLength / diameter * rho * velocity^2 / 2;
end WaterPipe;
