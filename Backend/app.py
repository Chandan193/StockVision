from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)
CORS(app, origins="http://localhost:5173")  # Corrected CORS here explicitly.

model = pickle.load(open('lstm_model.pickle', 'rb'))

def load_all_stocks():
    stocks = ['APOLLO HOSPITALS.CSV', 'ADANI_PORTS.csv', 'ADANI_ENTERPRISES.CSV', 'BAJAJ_FINSERV.csv', 'BHARTI_AIRTEL.CSV', 'ASIAN PAINTS.CSV', 'BHARAT PETROLEUM.CSV', 'BAJAJ AUTO.csv', 'BAJAJ_FINANCE.csv', 'AXIS_BANK.CSV', 'MARUTI SUZUKI.CSV', 'SBI_LIFE.csv', 'TECH_MAHINDRA.CSV', 'ICICI_BANK.CSV', 'WIPRO.csv', 'TATA CONSULTANCY SERVICES.CSV', 'JSW STEEL.CSV', 'HINDALCO.csv', 'KOTAK_MAHINDRA.csv', 'HERO MOTOCORP.CSV', 'HINDUSTAN UNILEVER.CSV', 'POWERGRID.CSV', 'SUN_PHARMA.CSV', 'COAL INDIA.CSV', 'TITAN.csv', 'HCL_TECHNOLOIES.CSV', 'TATA MOTORS.CSV', 'NIFTY_50_STOCKS.csv', 'ULTRATECH CEMENT.CSV', 'HDFC_BANK.csv', 'BRITANNIA.csv', 'TATA STEEL.CSV', 'ITC.csv', 'GRASIM.CSV', 'EICHER MOTOTRS.CSV', 'INFOSYS.csv', 'HDFC_LIFE.csv', 'ONGC.CSV', 'UPL.csv', 'RELIANCE.csv', 'INDUS INDUSTRIES.csv', 'NESTLE.CSV', 'NTPC.CSV', 'DIVIS LAB.csv', 'CIPLA.CSV', 'TATA CONSUMER PRODUCTS.csv', 'SBI_BANK.csv']

    combined_df = pd.DataFrame()

    for stock in stocks:
        df = pd.read_csv(f'stocks_data/{stock}', parse_dates=['Date'], dayfirst=True)
        df = df.groupby('Date', as_index=False)['Close'].mean()
        df.set_index('Date', inplace=True)
        combined_df[stock] = df['Close']

    combined_df.dropna(inplace=True)
    return combined_df

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    stock = data['stock']
    start = pd.to_datetime(data['start'])
    end = pd.to_datetime(data['end'])

    df_all = load_all_stocks()

    if stock not in df_all.columns:
        return jsonify({"error": f"Stock '{stock}' not found in data."}), 400

    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df_all)

    dates = pd.date_range(start, end)
    window = 60
    predictions = []

    for current_date in dates:
        if current_date not in df_all.index:
            continue

        idx_arr = df_all.index.get_indexer([current_date], method='nearest')
        idx = idx_arr[0]

        if idx < window:
            continue

        input_seq = scaled_data[idx - window:idx]
        input_seq = np.expand_dims(input_seq, axis=0)
        pred = model.predict(input_seq, verbose=0)
        pred_rescaled = scaler.inverse_transform(pred)[0]

        stock_idx = list(df_all.columns).index(stock)
        predicted_price = pred_rescaled[stock_idx]

        predictions.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "predicted_close": float(predicted_price)
        })

    return jsonify({"predictions": predictions})

if __name__ == "__main__":
    app.run(debug=True)
