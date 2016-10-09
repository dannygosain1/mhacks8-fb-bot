$.getJSON("/Graph", function(data){
    chart1 = data['chart']
    series1 = data['series']
    title1 = data['title']
    xAxis1 = data['xAxis']
    yAxis1 = data['yAxis']
    $("#container").highcharts({
        chart: chart1,
        title: title1,
        xAxis: xAxis1,
        yAxis: yAxis1,
        series: series1
    });
})