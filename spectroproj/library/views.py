from django.shortcuts import render, redirect
from django.http import HttpResponse
from collections import OrderedDict
from django.utils import timezone
from .models import *
from .fusioncharts import FusionCharts
from .forms import MeasurementForm
from django.db import connections
import logging, re, regex

logger = logging.getLogger(__name__)

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

    if (len(measurementSequence) > 0):

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

def addMeasurement(request):
    form = MeasurementForm
    
    if request.method == 'POST':
        form = MeasurementForm(request.POST)
    #if form.is_valid():
        #with open('readme.txt') as f:
        #lines = form.data['myFile'].readlines()

        #login_data = request.POST.dict()
        file = request.FILES['file']
        #file = login_data.get("myFile")
        logger.error(str(type(file)))

        content = str(file.read().decode())

        #logger.error("HERE_HERE_HERE")

        logger.error(content)

        #form.save()

        #дёргаем процедуру для сохранения последовательности спектра
        errorString = ''

        cursor = connections['default'].cursor()
        try:
            if (isContentValid(content) == True):

              #measurementSequenceString = re.sub(r',$', ' ', re.sub(r'(\d*)[.](\d*)\s(\d*)[.](\d*)', r'(\1.\2,\3.\4),', content).replace('\r\n', ''))
              measurementSequenceString = regex.sub(r',$', ' ', regex.sub(r'(\d+)([.](\d+)){0,1}\s(\d+)([.](\d+)){0,1}', r'(\1\2,\4\5),', content).replace('\r\n', ''))
              logger.error(measurementSequenceString)

              cursor.execute('EXEC [dbo].[MeasurementSequence@Add] @debug = 2, @measurementSequence = \'' + measurementSequenceString + '\'')

              records = cursor.fetchall()
              errorString = records[0][0]
            else:
              errorString = "Невірний формат завантаженого файлу."

            if (errorString != ''):
              return render(request, 'error.html', { 'errorString': errorString })
        finally:
            cursor.close()

        return redirect('measurements_list')
    context = {'form':form}
    return render(request, 'add-measurement.html', context)

def isContentValid(content):
  return regex.match(r'^(\d+([.]\d+){0,1}\s\d+([.]\d+){0,1}\r\n)+$', content, regex.MULTILINE) is not None