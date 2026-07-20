"""Single entrypoint: regenerates the full synthetic dataset under output/."""

import generate_transactions
import generate_planning_data

if __name__ == "__main__":
    generate_transactions.generate()
    generate_planning_data.generate_exchange_rates()
    generate_planning_data.generate_budgets()
    generate_planning_data.generate_commitments()
    generate_planning_data.generate_users()
