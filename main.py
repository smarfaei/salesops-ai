import json
from pathlib import Path


DATA_FILE = Path("leads.json")


def load_leads():
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_leads(leads):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            leads,
            file,
            indent=2,
            ensure_ascii=False
        )

def get_integer_input(message):
    while True:
        try:
            value = int(input(message))

            if value < 0:
                print("Please enter a positive number.")
                continue

            return value

        except ValueError:
            print("Invalid input. Please enter a number.")

def collect_lead():
    name = input("Customer name: ")
    company = input("Company name: ")

    employees = get_integer_input(
        "Number of employees: "
    )

    need = input(
        "What does the customer need? "
    )

    budget = get_integer_input(
        "Customer budget in USD: "
    )

    lead = {
        "name": name,
        "company": company,
        "employees": employees,
        "need": need,
        "budget": budget
    }

    return lead


def calculate_score(lead):
    score = 0

    if lead["budget"] >= 5000:
        score += 50
    elif lead["budget"] >= 2000:
        score += 30
    elif lead["budget"] >= 1000:
        score += 15

    if lead["employees"] >= 100:
        score += 30
    elif lead["employees"] >= 20:
        score += 20
    elif lead["employees"] >= 5:
        score += 10

    if "AI" in lead["need"].upper():
        score += 20

    return score


def get_status(score):
    if score >= 70:
        return "Hot Lead"
    elif score >= 40:
        return "Warm Lead"
    else:
        return "Cold Lead"


def add_lead():
    lead = collect_lead()

    score = calculate_score(lead)
    status = get_status(score)

    lead["score"] = score
    lead["status"] = status

    leads = load_leads()
    leads.append(lead)

    save_leads(leads)

    print("\nLead saved successfully.")
    print("Score:", score)
    print("Status:", status)


def show_all_leads():
    leads = load_leads()

    if not leads:
        print("\nNo leads found.")
        return

    print("\n--- All Leads ---")

    for index, lead in enumerate(leads, start=1):
        score = lead.get("score")

        if score is None:
            score = calculate_score(lead)

        status = lead.get("status")

        if status is None:
            status = get_status(score)

        print(f"\nLead #{index}")
        print("Name:", lead.get("name", "Unknown"))
        print("Company:", lead.get("company", "Unknown"))
        print("Need:", lead.get("need", "Unknown"))
        print("Budget: $", lead.get("budget", 0))
        print("Score:", score)
        print("Status:", status)

def show_hot_leads():
    leads = load_leads()

    hot_leads = []

    for lead in leads:
        score = lead.get("score")

        if score is None:
            score = calculate_score(lead)

        status = lead.get("status")

        if status is None:
            status = get_status(score)

        if status == "Hot Lead":
            lead["score"] = score
            lead["status"] = status
            hot_leads.append(lead)

    if not hot_leads:
        print("\nNo hot leads found.")
        return

    print("\n--- Hot Leads ---")

    for index, lead in enumerate(hot_leads, start=1):
        print(f"\nHot Lead #{index}")
        print("Name:", lead.get("name", "Unknown"))
        print("Company:", lead.get("company", "Unknown"))
        print("Budget: $", lead.get("budget", 0))
        print("Score:", lead["score"])


def show_menu():
    print("\n========================")
    print("AI Sales Agent")
    print("========================")
    print("1. Add new lead")
    print("2. Show all leads")
    print("3. Show hot leads")
    print("4. Exit")


def main():
    while True:
        show_menu()

        choice = input("\nChoose an option: ")

        if choice == "1":
            add_lead()

        elif choice == "2":
            show_all_leads()

        elif choice == "3":
            show_hot_leads()

        elif choice == "4":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid option. Please choose 1 to 4.")


main()