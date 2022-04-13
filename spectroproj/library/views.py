from django.shortcuts import render
from django.http import HttpResponse
from collections import OrderedDict
from django.utils import timezone
from .models import Measurement, MeasurementSequence
from .fusioncharts import FusionCharts

def measurements_list(request):
  dataSource = OrderedDict()

  chartConfig = OrderedDict()
  chartConfig["caption"] = "Spectro"
  chartConfig["subCaption"] = "In CU — conventional units"
  chartConfig["xAxisName"] = "Wave length"
  chartConfig["yAxisName"] = "Intensity (In CU)"
  chartConfig["numberSuffix"] = ""
  chartConfig["theme"] = "fusion"
  chartConfig["drawAnchors"] = False
  chartConfig["exportEnabled"] = False

  output = []

  #getting all measurements
  measurements = Measurement.objects.all().order_by('-date')

  for measurement in measurements:

    #getting full measurement sequence
    measurementSequence = MeasurementSequence.objects.filter(measurementID = measurement.ID).order_by('waveLength')

    dataSource["chart"] = chartConfig
    dataSource["dataset"] = []
    data = []

    for lengthIntensityPair in measurementSequence:
        data.append({"x": str(lengthIntensityPair.waveLength), "y": str(lengthIntensityPair.intensity)})

    dataSource["categories"] = [
        {
            "category": [
                {
                    "x": str(measurementSequence[0].waveLength),
                    "label": str(measurementSequence[0].waveLength),
                    "showverticalline": "0"
                },
                {
                    "x": str(measurementSequence[len(measurementSequence) - 1].waveLength),
                    "label": str(measurementSequence[len(measurementSequence) - 1].waveLength),
                    "showverticalline": "0"
                }
            ]
        }
    ]

    dataSource["dataset"].append({"data": data, 
        "seriesname": "Spectro",
            "showregressionline": "0",
            "drawLine": "1"})

    scatter = FusionCharts("scatter", "chart" + str(measurement.ID), "400", "400", "chartContainer" + str(measurement.ID), "json", dataSource)

    output.append({"graph": scatter.render(), "ID": measurement.ID})

  return render(request, 'measurements_list.html', {
    'output': output
})