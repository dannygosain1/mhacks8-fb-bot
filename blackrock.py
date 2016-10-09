import requests
import json
import ystockquote
import random

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

def getResponseData(url):
    response = requests.post(url, headers=headers)
    data = json.loads(response.text)
    return data

def getStockInfo(data):
    fields = ['ticker', 'description', 'assetClass', 'countryCode', 'cusip', 'currency', 'peRatio', 'gics1Sector']
    info = {}
    element = data['resultMap']['SECURITY'][-1]
    if element['success'] is True:
        for key in fields:
            info[key] = element[key]
    return info

def getSearchURL(ticker):
    return 'https://www.blackrock.com/tools/hackathon/security-data?identifiers=' + ticker +'&includePrices=true&query=' + ticker

def getAnalysisURL (positions,scenario):
    # positions: AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C
    # scenario: HIST_20081102_20080911%2CHIST_20110919_20110720%2CHIST_20130623_20130520%2CHIST_20140817_20140101%2CUS10Y_1SD%3A%3AAPB%2CINF2Y_1SD%3A%3AAPB%2CUSIG_1SD%3A%3AAPB%2CSPX_1SD%3A%3AAPB%2CDXY_1SD%3A%3AAPB
    return 'https://www.blackrock.com/tools/hackathon/portfolio-analysis?betaPortfolios=SNP500&calculateExposures=true&' \
           'calculatePerformance=true&calculateRisk=true&calculateStressTests=true&positions=' + positions + \
           '&riskFreeRatePortfolio=LTBILL1-3M&' \
           'scenarios=' + scenario + '&useCache=true'

def getYahooPrices(ticker):
    prices = []
    yahoo_data = ystockquote.get_historical_prices(ticker, '2016-09-01', '2016-10-08')
    for dates in yahoo_data:
        prices.append(yahoo_data[dates]['Close'])
    return prices

def insertPortfolio(values):
    return True

def updatePortfolio(data,ticker,quantity):
    data['quantity'] = data['quantity'] + quantity
    prices = getYahooPrices(ticker)
    data['price'] = prices[random.randrange(0, len(prices) - 1) % (len(prices) - 1)]
    # if quantity is 0:
    #     delete
    # else:
    #
    return True

def getPortfolio():
    tempjson = {}
    return tempjson

def createPositionString():
    # positions: AAPL~25%7CVWO~25%7CAGG~25%7CMALOX~25%7C
    portfolio = getPortfolio()
    positions = ''
    totalMV = [x['price']*x['quantity'] for x in portfolio]
    for elements in portfolio:
        positions = positions + elements['ticker'] + '~' + str(round(elements['price']*elements['quantity']/totalMV,1)) + str('%7C')
    return positions

def addPortfolio(ticker,quantity):
    url = getSearchURL(ticker)
    data = getResponseData(url)
    info = getStockInfo(data)
    info['quantity'] = quantity
    prices = getYahooPrices(ticker)
    info['price'] = prices[random.randrange(0,len(prices) - 1) % (len(prices) - 1)]
    if not info or quantity is 0:
        return False
    else:
        return insertPortfolio(info)

def portfolio(ticker,quantity,type):
    if type is 'sell':
        quantity = -quantity
    oldPortfolio = getPortfolio()
    if not oldPortfolio:
        return addPortfolio(ticker,quantity)
    else:
        if ticker in list(oldPortfolio['ticker']):
            return updatePortfolio(oldPortfolio['ticker'],ticker,quantity)
        else:
            return addPortfolio(ticker,quantity)

# print getYahooPrices('AGG')

# with open('data') as data_file:
#     data = json.load(data_file)
#
# for key in data['riskData']['scenariosInfo']:
#     print key + '|' + data['riskData']['scenariosInfo'][key]['description']