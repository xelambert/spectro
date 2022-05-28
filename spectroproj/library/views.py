from django.shortcuts import render, redirect
from django.http import HttpResponse
from collections import OrderedDict
from django.utils import timezone
from .models import *
from .fusioncharts import FusionCharts
from .forms import MeasurementForm
from django.db import connections
import logging, re, regex
import numpy as np
import scipy.signal
from scipy.signal import lfilter

logger = logging.getLogger(__name__)

def measurements_list(request):
  if (not request.user.is_authenticated):
    return redirect('../login')

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
    if (not request.user.is_authenticated):
      return redirect('../login')

    form = MeasurementForm
    
    if request.method == 'POST':
        form = MeasurementForm(request.POST)
        file = request.FILES['file']
        #logger.error(str(type(file)))

        content = str(file.read().decode())

        #logger.error(content)

        #дёргаем процедуру для сохранения последовательности спектра
        errorString = ''

        cursor = connections['default'].cursor()
        try:
            if (isContentValid(content) == True):
              measurementSequenceString = regex.sub(r',$', ' ', regex.sub(r'(\d+)([.](\d+)){0,1}\s(\d+)([.](\d+)){0,1}', r'(\1\2,\4\5),', content).replace('\r\n', ''))
              logger.error(measurementSequenceString)

              cursor.execute('EXEC [dbo].[MeasurementSequence@Add] @debug = 0, @measurementSequence = \'' + measurementSequenceString + '\'')

              records = cursor.fetchall()
              errorString = records[0][0]
            else:
              errorString = "Невірний формат завантаженого файлу."

            if (errorString != ''):
              return render(request, 'error.html', { 'errorString': errorString })
        finally:
            cursor.close()

        return redirect('../measurements_list') #redirect('measurements_list')
    context = {'form':form}
    return render(request, 'add-measurement.html', context)

def measurementDetails(request):
  if (not request.user.is_authenticated):
    return redirect('../login')

  hasEditRights = False

  if (request.user.username == 'su'):
    hasEditRights = True

  params = {'id': '',}
 

  if request.method == 'POST':
    #logger.error(request.POST['action'])
    if (request.POST['action'] == 'save'):

      #logger.error(request.POST)

      params['id'] = request.POST['id']
      params['name'] = request.POST['name']
      params['nameSpectrometer'] = request.POST['nameSpectrometer']
      params['typeSpectrometer'] = request.POST['typeSpectrometer']
      params['range'] = request.POST['range']
      params['filter'] = request.POST['filter']

      paramsString = ' SET name = \'\'' + params['name'] + '\'\''
      paramsString += ' ,nameSpectrometer = \'\'' + params['nameSpectrometer'] + '\'\''
      paramsString += ' ,typeSpectrometer = \'\'' + params['typeSpectrometer'] + '\'\''
      paramsString += ' ,range = \'\'' + params['range'] + '\'\''
      paramsString += ' ,filter = \'\'' + params['filter'] + '\'\''
      paramsString += ' WHERE id = ' + params['id']
      #logger.error(id)

      #logger.error(params.id)
      cursor = connections['default'].cursor()
      try:
          #if (isContentValid(content) == True):
          #logger.error('EXEC [dbo].[Measurement@Edit] @debug = 0, @params = ' + paramsString)

          cursor.execute('EXEC [dbo].[Measurement@Edit] @debug = 0, @params = \'' + paramsString + '\'')



          records = cursor.fetchall()
          errorString = records[0][0]
          #else:
            #errorString = "Невірний формат завантаженого файлу."

          if (errorString != ''):
            return render(request, 'error.html', { 'errorString': errorString })
      finally:
          cursor.close()

      
    else:
      params['id'] = request.POST['id']

      Measurement.objects.filter(ID = params['id']).delete()

    return redirect('measurements_list')

  measurementID = request.GET['id']

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

  measurement = Measurement.objects.get(ID = measurementID)

  params['id'] = measurement.ID
  params['date'] = str(measurement.date or '')
  params['name'] = str(measurement.name or '')
  params['nameSpectrometer'] = str(measurement.nameSpectrometer or '')
  params['typeSpectrometer'] = str(measurement.typeSpectrometer or '')
  params['range'] = str(measurement.range or '')
  params['filter'] = str(measurement.filter or '')

  #logger.error(params)

  #getting full measurement sequence
  measurementSequence = MeasurementSequence.objects.filter(measurementID = measurementID).order_by('waveLength')

  if (len(measurementSequence) > 0):
    vector = []
    peaksWaveLenghts = []

    dataSource["chart"] = chartConfig
    dataSource["dataset"] = []
    data = []

    for lengthIntensityPair in measurementSequence:
        data.append({"x": str(lengthIntensityPair.waveLength), "y": str(lengthIntensityPair.intensity)})
        vector.append(float(lengthIntensityPair.intensity))

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
                },            
            ]
        }
    ]

    dataSource["dataset"].append({"data": data, 
        "seriesname": "Spectro",
            "showregressionline": "0",
            "drawLine": "1"})


  n = 15  # the larger n is, the smoother curve will be
  b = [1.0 / n] * n
  a = 1
  yy = lfilter(b,a,vector)

  yyy = []
  counter = 0

  for val in vector:
    #smoothPart = counter/len(vector)
    #originalPart =  1 - smoothPart
    #yyy.append(vector[counter] * originalPart + yy[counter] * smoothPart)
    if (counter < 0.75 * len(vector)):
      yyy.append(vector[counter])
    else:
      yyy.append(yy[counter])
    counter += 1

  #plt.plot(x, yy, linewidth=2, linestyle="-", c="b")  # smooth by filter
  #print('Detect peaks without any filters.')
  #indexes = scipy.signal.find_peaks_cwt(vector, np.arange(1, 4),
     # max_distances=np.arange(1, 4)*2)
  #indexes, _ = scipy.signal.find_peaks(vector, height=200, width=3, prominence=200)
  #indexes, _ = scipy.signal.find_peaks(vector, height=200, width=3, prominence=120)
  #indexes, _ = scipy.signal.find_peaks(vector, height=200, prominence=110, width=3, wlen=20, threshold=10)
  indexes, _ = scipy.signal.find_peaks(yyy, width=3, prominence=120)
  logger.error('Peaks are: %s' % (indexes))

  peaksInfo = []
  info = [{"waveLength": "468.01", "text": "Спектральна лінія атому Цинку"},
  {"waveLength": "472.2", "text": "Спектральна лінія атому Цинку"},
  {"waveLength": "481.05", "text": "Спектральна лінія атому Цинку"},
  {"waveLength": "492.4", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "589.44", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "602.12", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "610.25", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "636.23", "text": "Спектральна лінія атому Цинку"},
  {"waveLength": "656.3", "text": "Спектральна лінія водню серії Бальмера Hα"},
  {"waveLength": "747.88", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "758.85", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "773.25", "text": "Спектральна лінія іона Цинку"},
  {"waveLength": "777.42", "text": "Спектральна лінія Кисню"},]

  counter = 0

  for index in indexes:
    counter += 1
    #peaksWaveLenghts.append(float(measurementSequence[index].waveLength))
    dataSource["categories"][int(0)]["category"].append({"x": str(measurementSequence[int(index)].waveLength), "label": str(measurementSequence[int(index)].waveLength), "showverticalline": "1", })
    peakInfoText = ""

    for infoEntry in info:
      if (abs(float(measurementSequence[int(index)].waveLength) - float(infoEntry["waveLength"])) <= 1.2):
        peakInfoText = infoEntry["text"]
    peaksInfo.append({"waveLength": str(measurementSequence[int(index)].waveLength), "info": peakInfoText,})
    #logger.error(dataSource["categories"])

  logger.error(dataSource["categories"][int(0)]["category"])

  scatter = FusionCharts("scatter", "chart" + str(measurementID), "1500", "400", "chartContainer" + str(measurementID), "json", dataSource)

  output.append({"graph": scatter.render(), "ID": measurementID, "peaksInfo": peaksInfo})

  #logger.error(str(measurementID))
  #logger.error((output[0]))



  
  return render(request, 'measurement_details.html', {'hasEditRights': hasEditRights, 'output': output[0], "params": params} )

def isContentValid(content):
  return regex.match(r'^(\d+([.]\d+){0,1}\s\d+([.]\d+){0,1}\r\n)+$', content, regex.MULTILINE) is not None