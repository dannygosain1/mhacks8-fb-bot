import requests
import json
import traceback
import ystockquote
import random
import app

# url = 'https://www.blackrock.com/tools/api-tester/hackathon?apiType=searchSecurities&query=GOOG'
# url = 'https://www.blackrock.com/tools/hackathon/search-securities?query=GOOG&useCache=true'
# url = 'https://www.blackrock.com/tools/api-tester/hackathon?apiType=securityData&identifiers=GOOG&includePrices=true&query=GOOG&useCache=true'
# url = 'https://www.blackrock.com/tools/hackathon/security-data?identifiers=GOOG&includePrices=true&query=GOOG'
# url = 'https://www.blackrock.com/tools/api-tester/hackathon?apiType=portfolioAnalysis&betaPortfolios=SNP500&calculateExposures=true&calculatePerformance=true&calculateRisk=true&calculateStressTests=true&positions=AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C&riskFreeRatePortfolio=LTBILL1-3M&scenarios=HIST_20081102_20080911%2CHIST_20110919_20110720%2CHIST_20130623_20130520%2CHIST_20140817_20140101%2CUS10Y_1SD%3A%3AAPB%2CINF2Y_1SD%3A%3AAPB%2CUSIG_1SD%3A%3AAPB%2CSPX_1SD%3A%3AAPB%2CDXY_1SD%3A%3AAPB&useCache=true'
# url = 'https://www.blackrock.com/tools/hackathon/portfolio-analysis?betaPortfolios=SNP500&calculateExposures=true&calculatePerformance=true&calculateRisk=true&calculateStressTests=true&positions=AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C&riskFreeRatePortfolio=LTBILL1-3M&scenarios=HIST_20081102_20080911%2CHIST_20110919_20110720%2CHIST_20130623_20130520%2CHIST_20140817_20140101%2CUS10Y_1SD%3A%3AAPB%2CINF2Y_1SD%3A%3AAPB%2CUSIG_1SD%3A%3AAPB%2CSPX_1SD%3A%3AAPB%2CDXY_1SD%3A%3AAPB&useCache=true'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
    'Content-Type': 'text/html',
}

scenarioFields = ['MS_US','MS_USD_DN','MS_USYC_UP','RAPID_DF','MSVIX_up','MS_USCPIUP']

def getResponseData(url):
    response = requests.post(url, headers=headers)
    data = json.loads(response.text)
    return data

def getStockInfo(data):
    fields = ['ticker', 'description', 'assetClass', 'countryCode', 'cusip', 'currency', 'gics1Sector']
    info = {}
    element = data['resultMap']['SECURITY'][-1]
    if element['success'] is True:
        for key in fields:
            try:
                info[key] = element[key]
            except Exception as e:
                app.log(traceback.print_exc())
                pass
    return info

def getSearchURL(ticker):
    return 'https://www.blackrock.com/tools/hackathon/security-data?identifiers=' + ticker +'&includePrices=true&query=' + ticker

def getAnalysisURL (positions,scenario):
    # positions: AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C
    # scenario: HIST_20081102_20080911%2CHIST_20110919_20110720%2CHIST_20130623_20130520%2CHIST_20140817_20140101%2CUS10Y_1SD%3A%3AAPB%2CINF2Y_1SD%3A%3AAPB%2CUSIG_1SD%3A%3AAPB%2CSPX_1SD%3A%3AAPB%2CDXY_1SD%3A%3AAPB
    # betaPortfolios=SNP500&
    # &riskFreeRatePortfolio=LTBILL1-3M&

    if scenario == '':
        return 'https://www.blackrock.com/tools/hackathon/portfolio-analysis?calculateExposures=true&' \
               'calculatePerformance=true&calculateRisk=true&calculateStressTests=true&positions=' + positions + '&useCache=true'
    else:
        return 'https://www.blackrock.com/tools/hackathon/portfolio-analysis?betaPortfolios = SNP500&calculateExposures=true' \
           '&calculatePerformance=true&calculateRisk=true&calculateStressTests=true&positions=' + positions + \
           '&riskFreeRatePortfolio = LTBILL1 - 3M&scenarios=' + scenario + '&useCache=true'

def getYahooPrices(ticker):
    prices = []
    yahoo_data = ystockquote.get_historical_prices(ticker, '2016-09-01', '2016-10-08')
    for dates in yahoo_data:
        prices.append(yahoo_data[dates]['Close'])
    return prices

def insertPortfolioDB(data,senderID):
    app.send_create_message(senderID,data)
    return True

def deletePortfolioDB(ticker,senderID):
    app.send_delete_message(senderID,ticker)
    return True

def updatePortfolioDB(data,senderID):
    app.send_update_message(senderID,data)
    return True

def getPortfolio():
    tempjson = app.get_portfolio()
    return tempjson

def updatePortfolio(data,ticker,quantity,senderID):
    data['quantity'] = int(str(data['quantity'])) + int(str(quantity))
    prices = getYahooPrices(ticker)
    data['price'] = float(prices[random.randrange(0, len(prices) - 1) % (len(prices) - 1)])
    if data["quantity"] is not 0:
        updatePortfolioDB(data,senderID)
    else:
        deletePortfolioDB(ticker, senderID)
    return True

def getPositionString():
    # positions: AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C
    portfolio = getPortfolio()
    positions = ''
    totalMV = sum([x['price']*x['quantity'] for x in portfolio])
    for elements in portfolio:
        positions = positions + elements['ticker'] + '~' + str(round(elements['price']*elements['quantity']*100/totalMV,1)) + str('%7C')
    return positions

def getScenarioString(scenario):
    # scenario: HIST_20081102_20080911%2CHIST_20110919_20110720%2CHIST_20130623_20130520%2CHIST_20140817_20140101%2CUS10Y_1SD%3A%3AAPB%2CINF2Y_1SD%3A%3AAPB%2CUSIG_1SD%3A%3AAPB%2CSPX_1SD%3A%3AAPB%2CDXY_1SD%3A%3AAPB
    scenarioString = ''
    if len(scenario) > 0:
        if '::' in scenario:
            scenario.replace(':', '%3A')
        scenarioString = scenarioString + scenario + str('%2C')
    return scenarioString

def addPortfolio(ticker,quantity,senderID):
    url = getSearchURL(ticker)
    data = getResponseData(url)
    info = getStockInfo(data)
    if not info or quantity == 0:
        return False
    else:
        info['quantity'] = int(quantity)
        prices = getYahooPrices(ticker)
        info['price'] = float(prices[random.randrange(0, len(prices) - 1) % (len(prices) - 1)])
        return insertPortfolioDB(info,senderID)

def getAnalysisResult(data, type):
    return data['resultMap']['PORTFOLIOS'][0]['portfolios'][0][type]

def getAnalyticsMap (data,field):
    # field: effectiveDuration, returnOnAssets
    return getAnalysisResult(data,'analyticsMap')[field]['value']

def getReturns(data,field):
    # field: capitalGainReturnY1, grossReturnY10, rnrRiskRatingOverall
    # return getAnalysisResult(data,'returns')['weightedAveragePerformance'][field]
    # field: twoYearRisk, oneYearAnnualized
    return getAnalysisResult(data, 'returns')['latestPerf'][field]

def getRiskData(data,field):
    # field: riskEquity, riskFixedIncome
    return getAnalysisResult(data, 'riskData')['riskFactorsMap'][field]['standalone']

def analyzePortfolio(scenario,type,field):
    positions = getPositionString()
    scenarioString = getScenarioString(scenario)
    url = getAnalysisURL(positions,scenarioString)
    print url
    data = getResponseData(url)
    if (type == 'RISK'):
        return getRiskData(data,field)
    elif (type == 'RETURNS'):
        return getReturns(data,field)
    elif (type == 'ANALYTICS'):
        return getAnalyticsMap(data,field)
    return ''

def portfolio(ticker,quantity,type,senderID):
    quantity = int(str(quantity))
    if type == 'SELL':
        quantity = -quantity
    oldPortfolio = getPortfolio()
    if not oldPortfolio:
        return addPortfolio(ticker,quantity,senderID)
    else:
        print oldPortfolio
        tickers = [str(x['ticker']) for x in oldPortfolio]
        if ticker in tickers:
            for y in oldPortfolio:
                if str(y['ticker']) == ticker:
                    print y
                    return updatePortfolio(y,ticker,quantity,senderID)
        else:
            return addPortfolio(ticker,quantity,senderID)

# portfolio('GOOG',10,'BUY',10)
# print getYahooPrices('AGG')

# with open('data') as data_file:
#     data = json.load(data_file)
#
# for key in data['riskData']['scenariosInfo']:
#     print key + '|' + data['riskData']['scenariosInfo'][key]['description']