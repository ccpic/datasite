from django.shortcuts import render
import pandas as pd

def index(request):
    return render(request, 'forecast/linear.html')


def ajax_process(request):
    html_string=request.GET['html_string']
    df = pd.read_html(html_string)[0]
    print(df)
    return None
