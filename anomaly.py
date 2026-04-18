# Simulated user transaction history
user_transactions = {}

def log_transaction(transaction):
    user_id = transaction.user_id

    if user_id not in user_transactions:
        user_transactions[user_id] = []

    user_transactions[user_id].append(transaction)


def detect_anomalies(user_id):
    if user_id not in user_transactions:
        return ["No transaction history"]

    transactions = user_transactions[user_id]

    if len(transactions) < 2:
        return ["Not enough data for anomaly detection"]

    anomalies = []

    # Calculate average spending
    amounts = [t.amount for t in transactions]
    avg_amount = sum(amounts) / len(amounts)

    # Latest transaction
    latest = transactions[-1]

    # Rule 1: Spike detection
    if latest.amount > 2 * avg_amount:
        anomalies.append("Spending spike detected")

    # Rule 2: New category
    categories = [t.category for t in transactions[:-1]]
    if latest.category not in categories:
        anomalies.append("New category detected")

    return anomalies


# 🔥 NEW: transaction history
def get_user_transactions(user_id):
    if user_id not in user_transactions:
        return []

    return [
        {
            "amount": t.amount,
            "category": t.category,
            "timestamp": t.timestamp
        }
        for t in user_transactions[user_id]
    ]