import math

def progressbar(perc):
  percentage = math.floor(perc / 10)
  progressbar = []

  for p in range(0, percentage):
    progressbar.append('🟥')

  for i in range(0, 10-percentage):
    progressbar.append('⬜️')
    
  progressbar.append(f' {round(perc)}%')

  return ''.join(progressbar)