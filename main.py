from refinedBase import *
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from time import time, sleep
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import os

TEST = False
FILE_PATH = "./data3.csv"

STOCKS = {
	"Technology": [
		("NVIDIA", "NVDA"),
		("Microsoft", "MSFT"),
		("Apple", "AAPL"),
		("Amazon", "AMZN"),
		("Broadcom", "AVGO"),
		("Tesla", "TSLA"),
	],
	"Finance": [
		("JPMorgan Chase", "JPM"),
		("Bank of America", "BAC"),
		("Wells Fargo", "WFC"),
		("Visa", "V"),
		("Mastercard", "MA"),
		("Morgan Stanley", "MS"),
		("Goldman Sachs", "GS"),
		("Citi", "C")
	],
	"Trade and Services": [
		("Walmart", "WMT"),
		("Home Depot", "HD"),
		("Costco", "COST"),
		("CVS Health", "CVS"),
		("UnitedHealth Group", "UNH"),
	],
	"Manufacturing": [
		("General Electric", "GE"),
		("Deere & Co", "DE"),
		("Caterpillar", "CAT")
	],
	"Real Estate and Construction": [
		("D.R. Horton", "DHI"),
		("Lennar", "LEN"),
		("Emcor", "EME"),
		("PulteGroup", "PHM"),
	],
	"Industrial Applications and Services": [
		("Honeywell", "HON"),
		("3M", "MMM"),
		("Lockheed Martin", "LMT"),
		("Waste Management", "WM")
	],
	"Life Sciences": [
		("Eli Lilly", "LLY"),
		("Johnson & Johnson", "JNJ"),
		("Merck & Co.", "MRK"),
		("Pfizer", "PFE"),
		("AbbVie", "ABBV"),
		("Thermo Fisher Scientific", "TMO"),
		("Danaher", "DHR")
	],
	"Energy and Transportation": [
		("Exxon Mobil", "XOM"),
		("Chevron", "CVX"),
		("Shell", "SHEL"),
		("NextEra Energy", "NEE"),
		("ConocoPhillips", "COP"),
		("Duke Energy", "DUK"),
		("BP", "BP")
	]
}

class InvestorInfo(BaseModel):
    """Schema for extracting investor details."""
    startDate: str = Field(description="The investment start date formatted as 'YYYY-MM-DD'.")
    endDate: str = Field(description="The investment end date formatted as 'YYYY-MM-DD'.")
    budget: float = Field(description="The primary investment budget, extracted as a number without currency symbols.")
    salary: float = Field(description="The True Salary, extracted as a number without currency symbols. Use 0.0 if not explicitly mentioned.")
    categories: list[str] = Field(description="A list of financial or industry categories that the investor IS OPEN TO investing in. You MUST derive this list by starting with ALL available categories and then REMOVING any category the investor explicitly mentions they 'avoid' or 'dislike' (or similar negative context). Only have a maximum of THREE (3) categories. You MUST use categories ONLY from this predefined list: 'Technology', 'Finance', 'Trade and Services', 'Manufacturing', 'Real Estate and Construction', 'Industrial Applications and Services', 'Life Sciences', 'Energy and Transportation'. Use 'Real Estate and Construction' for 'real estate'.")

SYSTEM_INSTRUCTIONS = (
	"You are an expert financial data parser. Your task is to accurately extract "
	"the requested investor information from the provided text context. "
	"Strictly adhere to the following rules:\n"
	"1. Dates must be formatted as YYYY-MM-DD.\n"
	"2. Budget and Salary must be numeric (float) values. If salary is not given, use 0.0.\n"
	"3. Categories must be a list containing ONLY the specified allowed industry names. Do NOT insert industries which the investor does NOT LIKE "
	"Ignore hobbies, ages, and any other irrelevant information."
)

# Define the configuration for the structured output
CONFIG = types.GenerateContentConfig(
	system_instruction=SYSTEM_INSTRUCTIONS,
	response_mime_type="application/json",
	response_json_schema=InvestorInfo.model_json_schema(),
	
	# Thinking Configuration
	thinking_config=types.ThinkingConfig(thinking_budget=7000)
)

def createGeminiClient():
	# Define the Gemini client and the config
	client = genai.Client(api_key="AIzaSyDwF4oY4MIgZlUAaFDYzfI_vGnWUAeZrl0")

	return client

def getAllStocks():
	tickers = []

	for stockGroupName, stockGroup in STOCKS.items():
		for stock in stockGroup:
			tickers.append(stock[1])
	
	return tickers

def extractInfo(client: genai.Client, context: str) -> tuple[str, str, float, float, list[str]]:
	"""
	Extracts structured investor information from a context string using the Gemini API 
	with a Pydantic response schema.
	"""

	start = time()

	prompt = f"Extract the required data from the following context:\n\n{context}"
	
	response = client.models.generate_content(
		model='gemini-2.5-flash',  # Use a powerful model for structured extraction
		contents=prompt,
		config=CONFIG,
	)

	# Parse the JSON string output into the Pydantic model
	extracted_data = InvestorInfo.model_validate_json(response.text) # type: ignore

	end = time()
	
	# Return the data in the required tuple format
	return (
		extracted_data.startDate, 
		extracted_data.endDate, 
		extracted_data.budget, 
		extracted_data.salary, 
		extracted_data.categories,
		end - start
	) # type: ignore

def convertStringToDate(date):
	return datetime.strptime(date, '%Y-%m-%d')

def getDesiredTickers(groups):
	stockGroups = STOCKS.keys()
	tickers = []

	for group in groups:
		if group in stockGroups:
			for stock in STOCKS[group]:
				tickers.append(stock[1])
	
	return tickers

# def loadOrDownloadHistoricalData(tickers):
#     # 1. Check if the file exists
#     if os.path.isfile(FILE_PATH):
#         print(f"File found at {FILE_PATH}. Loading data from disk...")
#         try:
#             # Load the data, ensuring the first column (Date index) is parsed correctly
#             data = pd.read_csv(FILE_PATH, index_col=0, parse_dates=True)
#             # Ensure the loaded data matches the tickers requested (optional check)
#             if all(ticker in data.columns for ticker in tickers):
#                 print("Data loaded successfully.")
#                 return data
#             else:
#                 print("Loaded data does not match requested tickers. Re-downloading.")
#                 # If tickers do not match, proceed to download and overwrite
#         except Exception as e:
#             print(f"Error loading CSV file: {e}. File may be corrupted. Re-downloading.")
	
#     # 2. If file not found or load failed, proceed to download
	
#     # User's function handles dynamic start/end dates
#     downloadedData = downloadHistoricalData(tickers)
	
#     # 3. Save the newly downloaded data to disk
#     if not downloadedData.empty:
#         downloadedData.to_csv(FILE_PATH)
#         print(f"New data saved to disk at {FILE_PATH}.")
	
#     return downloadedData

def loadHistoricalData(tickers):
	# 1. Check if the file exists
	if not os.path.isfile(FILE_PATH):
		print(f"File not found at {FILE_PATH}. Please run the download function first.")
		return None

	print(f"File found at {FILE_PATH}. Loading data from disk...")
	
	try:
		# 2. Load the data, explicitly reading the two header rows to reconstruct the MultiIndex
		data = pd.read_csv(
			FILE_PATH, 
			index_col=0, 
			parse_dates=True,
			header=[0, 1],         # <--- FIX: Use the first two rows (index 0 and 1) as headers
			low_memory=False       # <--- FIX: Helps resolve DtypeWarning for large files
		)
		
		# 3. Validation Check: Ensure requested tickers are in the loaded data
		#    We get the tickers from the second level of the MultiIndex columns.
		loaded_tickers = set(data.columns.get_level_values(1))
		requested_tickers = set(tickers)
		
		if requested_tickers.issubset(loaded_tickers):
			print("Data loaded and validated successfully.")
		else:
			missing_tickers = requested_tickers - loaded_tickers
			print(f"Error: Loaded data is missing some requested tickers ({missing_tickers}). Data may be outdated.")
			
		return data

	except Exception as e:
		print(f"Error loading CSV file from {FILE_PATH}: {e}")
		# In a full program, you might call the download function here.
		return None

def downloadHistoricalData(tickers):
	startDate = datetime(2007, 1, 1, 0, 0, 0)
	endDate = datetime.now()
	
	# Configuration for safe downloading
	BATCH_SIZE = 50      # Number of tickers to download at once
	BASE_DELAY = 3.5     # Base waiting time between batches in seconds
	
	ticker_batches = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
	all_data = pd.DataFrame()
	
	end_date_str = (endDate + timedelta(days=1)).strftime('%Y-%m-%d')
	start_date_str = startDate.strftime('%Y-%m-%d')
	
	print(f"Starting batched download for {len(tickers)} tickers from {start_date_str} to {end_date_str}...")
	
	for i, batch in enumerate(ticker_batches):
		if i > 0:
			# Introduce a random delay to mitigate rate limiting
			wait_time = BASE_DELAY + np.random.uniform(0, 1.5)
			print(f"Waiting for {wait_time:.2f} seconds before next batch...")
			sleep(wait_time)
			
		print(f"Downloading batch {i+1}/{len(ticker_batches)} ({len(batch)} tickers)...")
		
		try:
			batch_data = yf.download(
				batch,
				start=start_date_str,
				end=end_date_str,
				progress=True # Set to False for cleaner batch output
			)[["Open", "Close"]] # type: ignore
			
			# Combine the new data with the existing data
			if all_data.empty:
				all_data = batch_data
			else:
				all_data = pd.concat([all_data, batch_data], axis=1)

		except Exception as e:
			# Catch other potential errors gracefully (e.g., connection issues)
			print(f"An unexpected error occurred during batch download: {e}")
			
	print(f"\nDownload finished. Retrieved data for {len(all_data.columns)} tickers.")
	return all_data

def getTopGainersUnderPrice(tickers, historicalData, maxPrice, startDate, endDate, topN=8):
	"""
	Calculates the percentage gain for all tickers between two specified dates, 
	filters by maxPrice (the price on the end date), and returns the top N gainers.
	
	NOTE: 'historicalData' must have a DatetimeIndex covering the date range.
	"""
	performance = []
	
	# 1. Slice the DataFrame to the exact period requested
	# We use .loc to slice the rows (dates) and avoid future SettingWithCopyWarning
	if not isinstance(historicalData.index, pd.DatetimeIndex):
		historicalData.index = pd.to_datetime(historicalData.index, format="%d/%m/%Y")
	indexSeries = historicalData.index.to_series()
	startDate = indexSeries.reindex([startDate], method='backfill').iloc[0]
	endDate = indexSeries.reindex([endDate], method='ffill').iloc[0]
	periodData = historicalData.loc[startDate:endDate].copy()
	
	# Get the last recorded date's prices for filtering (endPrice)
	latestPrices = periodData.iloc[-1].dropna()
	
	for ticker in tickers:
		# try:
		# Get only the prices for the current ticker within the period
		prices = periodData.xs(ticker, level=1, axis=1).dropna()
		
		if len(prices) < 2:
			continue
		
		endPrice = latestPrices.get(ticker)
		# print("xxxxxxxxx", prices)

		# Calculate gain using the first and last price in the sliced period
		startPrice = prices["Close"].iloc[0]
		endPrice = prices["Close"].iloc[-1]
		gainPercent = ((endPrice - startPrice) / startPrice) * 100

		performance.append({
			'ticker': ticker,
			'gainPercent': gainPercent,
			'endPrice': float(endPrice),
			'startPrice': float(startPrice)
		})

		# except Exception as e:
		# 	# Skip any ticker that causes an error (e.g., missing data)
		# 	print(e)
		# 	continue
			
	# Sort and select top N
	sortedPerformance = sorted(
		performance, 
		key=lambda x: x['gainPercent'], 
		reverse=True
	)
	
	return sortedPerformance[:topN]

def orderStocks(topStocks):
	stock1 = topStocks[0]
	stock2 = topStocks[1]
	
	# Compare end prices (the current buying price)
	if stock1['startPrice'] < stock2['startPrice']:
		return stock1, stock2
	elif stock2['startPrice'] < stock1['startPrice']:
		return stock2, stock1
	else:
		# If prices are equal, default to the one with the highest gain 
		# (which is stock1, as the input list is sorted by gain)
		return stock1, stock2

def allocateBudgetByGain(topStocks, trueBudget):
    if not topStocks:
        return []

    # 1. Calculate Total Gain and Weights
    # Sum up the gain percentage of all selected stocks
    totalGain = sum(stock['gainPercent'] for stock in topStocks)
    
    if totalGain == 0:
        # Avoid division by zero if all top stocks had zero gain
        return [{"ticker": stock["ticker"], "quantity": 1} for stock in topStocks]

    # Initialize variables for the budget allocation loop
    finalPortfolio = []
    remainingBudget = trueBudget
    
    # 2. Iteratively Allocate Budget and Determine Integer Quantities
    for stock in topStocks:
        ticker = stock['ticker']
        endPrice = stock['endPrice'] # Use endPrice as the current purchase price
        gainPercent = stock['gainPercent']
        
        # Calculate the proportional weight of this stock's gain relative to the total gain
        weight = gainPercent / totalGain
        
        # Determine the dollar amount to allocate based on this weight
        budgetAllocation = trueBudget * weight
        
        # Find the maximum integer quantity we can buy with the allocated budget
        if endPrice > 0:
            quantity = int(budgetAllocation // endPrice)
        else:
            quantity = 0

        # --- Refinement: Ensure budget isn't breached and quantity is positive ---
        if quantity > 0:
            cost = quantity * endPrice
            
            # If the calculated cost exceeds the actual remaining budget, 
            # recalculate based only on what's left. This is a crucial final check.
            if cost > remainingBudget:
                 quantity = int(remainingBudget // endPrice)
                 cost = quantity * endPrice
            
            if quantity > 0:
                finalPortfolio.append({
                    "ticker": ticker, 
                    "quantity": quantity
                })
                remainingBudget -= cost
                
    # 3. Handle leftover budget by giving 1 extra share to the top gainer (if budget allows)
    if remainingBudget > 0 and finalPortfolio:
        # Find the stock with the highest gain/rank (usually topStocks[0], but check the final list)
        topRankedTicker = topStocks[0]['ticker']
        
        # Find this stock in the finalPortfolio and check if we can afford 1 more share
        for item in finalPortfolio:
            if item["ticker"] == topRankedTicker:
                # Find its current price again
                topStockEndPrice = next(s['endPrice'] for s in topStocks if s['ticker'] == topRankedTicker)
                
                if remainingBudget >= topStockEndPrice:
                    item["quantity"] += 1
                    # remainingBudget -= topStockEndPrice # Not necessary to track for output

    return finalPortfolio

if __name__ == "__main__":
	client = createGeminiClient()
	historicalData = loadHistoricalData(getAllStocks())
	
	try:
		while True:
			try:
				print("\n==============================================================================\n")

				# Get the team information
				success, information = getMyCurrentInformation()
				if not success:
					print(f"Error 1: {information}")
				print(f"Team information: ", information)

				# Get the context request
				if TEST:
					success = True
					context = "Monica Pena is 75 years old and has a budget of $57121. She started investing on September 27th, 2020 and ended on August 24th, 2022. She enjoys rock climbing and avoids Manufacturing, Real Estate and Construction, Life Sciences, Energy and Transportation."
				else:
					success, context = getContext()

				if not success:
					print(f"Error 2: {context}")
				print(f"Context provided: {context}\n")

				# Extract the info from the context
				startDate, endDate, budget, salary, categories, timeTaken = extractInfo(client, context) # type: ignore
				print(f"Context details extracted ---")
				print(f"\tStart Date: {startDate} \n\tEnd Date: {endDate} \n\tBudget: {budget} \n\tSalary: {salary} \n\tCategories: {categories}")
				print(f"\tTime taken to extract context: {timeTaken}\n")

				# Convert the date strings to datetime objects
				startDate, endDate = convertStringToDate(startDate), convertStringToDate(endDate)
				trueBudget = budget * 0.9
				if budget == 0:
					trueBudget = salary * ((endDate - startDate).total_seconds() * (365 * 24 * 60 * 60)) * 0.9 # type: ignore
					if salary == 0:
						if not TEST:
							sendPortfolio([{ "ticker": "AAPL", "quantity": 1 }])

				# Get the desired tickers
				if categories == []:
					desiredTickers = getAllStocks()
				else:
					desiredTickers = getDesiredTickers(categories)

				# Choose the best stocks from the desired tickers
				topStocks = getTopGainersUnderPrice(desiredTickers, historicalData, trueBudget / 5, startDate, endDate)
				# print(trueBudget)
				# print(desiredTickers)
				# print(topStocks)
				# print(historicalData)

				order = allocateBudgetByGain(topStocks, trueBudget)

				print(f"Total Budget: ${trueBudget:.2f}")

				totalCost = sum(item["quantity"] * next(s["startPrice"] for s in topStocks if s["ticker"] == item["ticker"]) 
								for item in order)

				print(f"Total Portfolio Cost: ${totalCost:.2f}")
				print(f"Budget Remaining: ${trueBudget - totalCost:.2f}")

				print(f"Purchasing {order}")
				if not TEST:
					if order == []:
						success, response = sendPortfolio([{ "ticker": "AAPL", "quantity": 1 }])
					elif trueBudget - totalCost < 0:
						success, response = sendPortfolio([{ "ticker": "AAPL", "quantity": 1 }])
					else:
						success, response = sendPortfolio(order)

					if not success:
						print(f"Error 3: {response}")
					print(f"Evaluation response: {response}\n")

			except ZeroDivisionError as e:
				print(f"Exception: {e}")
				sleep(10)

	except KeyboardInterrupt:
		print("Exiting...")
		exit()
