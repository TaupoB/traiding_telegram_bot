import torch
import yfinance as yf

def load_data(ticker_list, period='1mo'):
    companies = {}
    for company in ticker_list:
        temp_ticker = yf.Ticker(company)
        temp = temp_ticker.history(period=period)['Close']
        temp.index = range(len(temp))
        companies[company] = temp
    return companies


class TickerModel(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers):
        super(TickerModel, self).__init__()
        self.num_layers = num_layers
        self.hidden_dim = hidden_dim
        self.gru = torch.nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc1 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, _ = self.gru(x)
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        out = self.relu(out)
        return out

class Model:

    def __init__(self, model_path):
        self.model = torch.load(model_path)
        self.model.eval()

    def predict_with_price(self, prices, alpha=0.00112):
        assert isinstance(prices, torch.FloatTensor), 'Must be torch.FloatTensor'

        if len(prices.shape) != 3:
            prices = prices.reshape(-1, 1).unsqueeze(0)

        pred_price = self.model(prices).item()

        prev = prices.reshape(-1)[-1]
        if abs((prev - pred_price) / pred_price) < alpha:
            return pred_price, 0
        elif (prev - pred_price) / pred_price >= alpha:
            return pred_price, 1
        elif (prev - pred_price) / pred_price <= -alpha:
            return pred_price, -1

    @staticmethod
    def convert_data(data):
        return torch.FloatTensor(data[-21:].values).reshape(-1, 1).unsqueeze(0)

    def predict(self, prices, alpha = 0.00112):
        prices = self.convert_data(prices)
        return self.predict_with_price(prices, alpha)[1]
