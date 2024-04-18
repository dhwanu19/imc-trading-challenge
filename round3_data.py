import csv
import matplotlib.pyplot as plt

mid_prices_choc = []
mid_prices_straw = []
mid_prices_roses = []
mid_prices_basket = []

# Specify the path to your CSV file
for file_path in ['data/prices_round_3_day_0.csv', 'data/prices_round_3_day_1.csv', 'data/prices_round_3_day_2.csv']:
    
    # Open the file in read mode
    with open(file_path, mode='r') as file:
        # Create a CSV reader object specifying the delimiter as ';'
        reader = csv.DictReader(file, delimiter=';')
    
        # Iterate over the reader object to process each row

        for row in reader:
            if row["product"] == "CHOCOLATE":
                mid_prices_choc.append(row["mid_price"])
            elif row["product"] == "STRAWBERRY":
                mid_prices_straw.append(row["mid_price"])
            elif row["product"] == "ROSES":
                mid_prices_roses.append(row["mid_price"])
            elif row["product"] == "GIFT_BASKET":
                mid_prices_basket.append(row["mid_price"])


# Plotting the values
plt.plot(mid_prices_choc)

# Adding labels and title
plt.xlabel('Index')

plt.title('Plot of Array Values')

# Display the plot
plt.show()

