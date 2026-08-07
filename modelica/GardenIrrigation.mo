model GardenIrrigation "Ustálený model gravitační kapkové závlahy"
  parameter Real tankWaterLevel(unit="m", min=0) = 1.0
    "Výška hladiny nad výtokem z IBC";
  parameter Real tankArea(unit="m2", min=0.1) = 2.0
    "Součet půdorysných ploch dvou IBC";
  parameter Real irrigationDuration(unit="s", min=1) = 3600;
  parameter Real filterHeadLoss(unit="m", min=0) = 0.2;
  parameter Real mainDiameter(unit="m", min=0.005) = 0.025;
  parameter Real rowDiameter(unit="m", min=0.003) = 0.0136;
  parameter Real dripperSpacing(unit="m", min=0.05) = 0.33;
  parameter Real nominalEmitterFlow(unit="m3/s", min=0) = 5.55555555555556e-7
    "2 l/h";
  parameter Real nominalEmitterPressure(unit="Pa", min=100) = 100000;
  parameter Real emitterExponent(min=0.1, max=1.5) = 0.5;
  parameter Real valveA(min=0, max=1) = 1;
  parameter Real valveB(min=0, max=1) = 1;
  parameter Real valveC(min=0, max=1) = 1;
  parameter Real valveD(min=0, max=1) = 1;
  parameter Real valveE(min=0, max=1) = 1;
  parameter Real valveF(min=0, max=1) = 1;
  parameter Real valveG(min=0, max=1) = 1;
  parameter Real valveH(min=0, max=1) = 1;
  parameter Real valveI(min=0, max=1) = 1;
  parameter Real valveJ(min=0, max=1) = 1;

  output Real totalFlow(unit="m3/s", min=0);
  output Real pressureAfterFilter(unit="Pa", min=0);
  output Real tankLevelEndEstimated(unit="m", min=0);
  output Real bedFlow[10](each unit="m3/s", each min=0);
  output Real rowFlow[10](each unit="m3/s", each min=0)
    "Průtok jedním ekvivalentním řádkem daného záhonu";
  output Real bedInletPressure[10](each unit="Pa", each min=0);
  output Real rowEndPressure[10](each unit="Pa", each min=0);
  output Real averageEmitterFlow[10](each unit="m3/s", each min=0);
  output Real waterDelivered[10](each unit="l", each min=0);

protected
  constant Real pi = 3.141592653589793;
  constant Real rho(unit="kg/m3") = 998.2;
  constant Real g(unit="m/s2") = 9.80665;
  parameter Real bedDrop[10](each unit="m") =
    {6.55, 4.55, 7.55, 6.55, 7.95, 7.05, 6.55, 3.70, 5.20, 5.20};
  parameter Integer rowCount[10] = {5, 6, 2, 5, 5, 5, 3, 3, 3, 3};
  parameter Real rowLength[10](each unit="m") =
    {6.0, 13.0, 14.0, 9.0, 3.0, 3.2, 2.5, 2.4, 1.7, 2.0};
  parameter Real opening[10] =
    {valveA, valveB, valveC, valveD, valveE,
     valveF, valveG, valveH, valveI, valveJ};
  parameter Real mainFriction = 0.025;
  parameter Real rowFriction = 0.030;
  parameter Real distributedOutletFactor = 0.35;
  parameter Real mainMinorLoss = 3.0;
  parameter Real zoneALength(unit="m") = 25;
  parameter Real zoneBLength(unit="m") = 15;
  parameter Real valveNominalFlow(unit="m3/s") = 0.0002;
  parameter Real valveNominalHeadLoss(unit="m") = 0.2;
  Real mainArea(unit="m2");
  Real rowArea(unit="m2");
  Real zoneFlowA(unit="m3/s");
  Real zoneFlowB(unit="m3/s");
  Real zoneVelocityA(unit="m/s");
  Real zoneVelocityB(unit="m/s");
  Real zoneLossA(unit="m");
  Real zoneLossB(unit="m");
  Real mainLoss[10](each unit="m");
  Real valveLoss[10](each unit="m");
  Real rowVelocity[10](each unit="m/s");
  Real rowHeadLoss[10](each unit="m");
  Real bedInletHead[10](each unit="m");
  Real averageEmitterHead[10](each unit="m");
  Real emitterCount[10];

equation
  mainArea = pi * mainDiameter^2 / 4;
  rowArea = pi * rowDiameter^2 / 4;
  zoneFlowA = sum(bedFlow[1:4]);
  zoneFlowB = sum(bedFlow[5:10]);
  zoneVelocityA = zoneFlowA / mainArea;
  zoneVelocityB = zoneFlowB / mainArea;
  zoneLossA = (mainFriction * zoneALength / mainDiameter + mainMinorLoss) *
    zoneVelocityA^2 / (2 * g);
  zoneLossB = (mainFriction * zoneBLength / mainDiameter + mainMinorLoss) *
    zoneVelocityB^2 / (2 * g);
  pressureAfterFilter = rho * g * max(0, tankWaterLevel - filterHeadLoss);

  for i in 1:10 loop
    emitterCount[i] = floor(rowLength[i] / dripperSpacing) + 1;
    mainLoss[i] = if i <= 4 then zoneLossA else zoneLossB;
    valveLoss[i] = if opening[i] > 0.0001 then
      valveNominalHeadLoss *
      (bedFlow[i] / (opening[i]^2 * valveNominalFlow))^2
      else tankWaterLevel + bedDrop[i] + 1;
    bedInletHead[i] = max(0, tankWaterLevel + bedDrop[i] -
      filterHeadLoss - mainLoss[i] - valveLoss[i]);
    rowVelocity[i] = rowFlow[i] / rowArea;
    rowHeadLoss[i] = rowFriction * rowLength[i] / rowDiameter *
      rowVelocity[i]^2 / (2 * g) * distributedOutletFactor;
    averageEmitterHead[i] = max(0, bedInletHead[i] - 0.5 * rowHeadLoss[i]);
    rowFlow[i] = if opening[i] > 0.0001 then
      emitterCount[i] * nominalEmitterFlow *
      (rho * g * averageEmitterHead[i] / nominalEmitterPressure)^emitterExponent
      else 0;
    bedFlow[i] = rowCount[i] * rowFlow[i];
    bedInletPressure[i] = rho * g * bedInletHead[i];
    rowEndPressure[i] = rho * g * max(0, bedInletHead[i] - rowHeadLoss[i]);
    averageEmitterFlow[i] = rowFlow[i] / emitterCount[i];
    waterDelivered[i] = bedFlow[i] * irrigationDuration * 1000;
  end for;

  totalFlow = sum(bedFlow);
  tankLevelEndEstimated = max(0,
    tankWaterLevel - totalFlow * irrigationDuration / tankArea);
end GardenIrrigation;
