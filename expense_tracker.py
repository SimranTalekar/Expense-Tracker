# Expense Tracker

import json
from pathlib import Path


database = "expense_tracker.json"
data = []

if Path(database).exists():
    with open(database, "r") as f:
        content = f.read()

        if content.strip():
            data = json.loads(content)

def save():
    with open(database, "w") as f:
        json.dump(data, f, indent=4)


class Budget:
   def __init__(self):
      budget = int(input("Enter your budget : "))


      print(f"Enter your monthly budget = Rs.{budget}/-")
      print("Budget successfully set .")

class User(Budget) :
   
    def add_expense(self) :
        date = input("Date : ")             # (DD/MM/YYYY)
        category = input("Category : ")
        amount = int(input("Amount : "))
        description = input("Description : ")

        expense = {
        "Date" : date ,
        "Category" : category ,
        "Amount" : amount , 
        "Description" : description ,
        }
        data.append(expense)
        save()
        print("Expense successfully added !!")

    def total_spending(self) :
        total = 0
        for exp in data:
          total += exp['Amount']
        print(f"Total spendings = Rs.{total}/-")

    
    def category_spending(self):
        food = 0
        transport = 0
        rent = 0
        education = 0
        shopping = 0
        others = 0

        for exp in data:
            if exp['Category'].lower() == "food":
                food += exp['Amount']

            elif exp['Category'].lower() == "transport":
                transport += exp['Amount']

            elif exp['Category'].lower() == "rent":
                rent += exp['Amount']

            elif exp['Category'].lower() == "education":
                education += exp['Amount']

            elif exp['Category'].lower() == "shopping":
                shopping += exp['Amount']

            elif exp['Category'].lower() == "others":
                others += exp['Amount']

            else:
                print("Invalid category:", exp['Category'])

        # Print the report after processing all expenses
        print("\n---------- Category-Wise Spending ----------")
        print(f"Food         : {food}")
        print(f"Transport    : {transport}")
        print(f"Rent         : {rent}")
        print(f"Education    : {education}")
        print(f"Shopping     : {shopping}")
        print(f"Others       : {others}")
        print("---------------------------------------------")


user = User()

while True :
   print("------------ WELCOME -----------\n\n")
   print("1.Add expense")
   print("2.View total spendings")
   print("3.View category-wise expense")
   print("4.Exit")


   choice = int(input("Enter your choice : "))

   if choice == 1 :
      user.add_expense()
   elif choice == 2:
      user.total_spending()
   elif choice == 3 :
      user.category_spending()
   elif choice == 4 :
      print("Thanks for using the app !!")
      break