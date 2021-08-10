from pyecharts.charts import Bar


def bargraph(x, y):
    bar = Bar()
    bar.add_xaxis(x)
    bar.add_yaxis("Visitor", y)
    bar.render('templates/Appointment/charts.html')
