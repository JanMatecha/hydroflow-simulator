model TwoTanks "Nestacionární proudění mezi dvěma otevřenými nádobami"
  parameter Real tank1Diameter(unit="m", min=0.05) = 0.8;
  parameter Real tank2Diameter(unit="m", min=0.05) = 0.8;
  parameter Real initialLevel1(unit="m", min=0.001) = 1.2;
  parameter Real initialLevel2(unit="m", min=0.001) = 0.3;
  parameter Real pipeLength(unit="m", min=0.01) = 3;
  parameter Real pipeDiameter(unit="m", min=0.0001) = 0.025;
  parameter Real roughness(unit="m", min=0) = 0.0000015;
  parameter Real temperatureC(unit="degC", min=0.01, max=95) = 20;
  parameter Real minorLossCoefficient(min=0) = 1.5
    "Součet vstupní a výstupní místní ztráty";

  output Real level1(unit="m", start=initialLevel1);
  output Real level2(unit="m", start=initialLevel2);
  output Real velocity(unit="m/s", start=0);
  output Real volumeFlow(unit="m3/s");
  output Real reynolds(min=0);
  output Real frictionFactor(min=0);
  output Real pressureDifference(unit="Pa");
  output Real rho(unit="kg/m3");
  output Real mu(unit="Pa.s");

protected
  constant Real pi = 3.141592653589793;
  constant Real gravity(unit="m/s2") = 9.80665;
  Real tank1Area(unit="m2");
  Real tank2Area(unit="m2");
  Real pipeArea(unit="m2");
  Real speedMagnitude(unit="m/s");
  Real pipeLossAcceleration(unit="m/s2");

initial equation
  level1 = initialLevel1;
  level2 = initialLevel2;
  velocity = 0;

equation
  // Praktické aproximace vlastností kapalné vody.
  rho = 1000 * (1 - ((temperatureC + 288.9414) /
    (508929.2 * (temperatureC + 68.12963))) * (temperatureC - 3.9863)^2);
  mu = 0.00002414 * 10^(247.8 / (temperatureC + 133.15));

  tank1Area = pi * tank1Diameter^2 / 4;
  tank2Area = pi * tank2Diameter^2 / 4;
  pipeArea = pi * pipeDiameter^2 / 4;
  volumeFlow = pipeArea * velocity;

  der(level1) = -volumeFlow / tank1Area;
  der(level2) = volumeFlow / tank2Area;

  speedMagnitude = noEvent(abs(velocity));
  reynolds = rho * speedMagnitude * pipeDiameter / mu;
  frictionFactor = noEvent(if reynolds < 1e-8 then 0
    elseif reynolds < 2300 then 64 / reynolds
    else 0.25 / (log10(roughness / (3.7 * pipeDiameter) +
      5.74 / reynolds^0.9))^2);
  pipeLossAcceleration = noEvent(if reynolds < 2300 then
    32 * mu / (rho * pipeDiameter^2) * velocity
    else frictionFactor / (2 * pipeDiameter) * velocity * speedMagnitude);

  // Nestacionární Bernoulliho rovnice mezi volnými hladinami.
  der(velocity) = gravity / pipeLength * (level1 - level2) -
    pipeLossAcceleration - minorLossCoefficient / (2 * pipeLength) *
    velocity * speedMagnitude;
  pressureDifference = rho * gravity * (level1 - level2);
end TwoTanks;
