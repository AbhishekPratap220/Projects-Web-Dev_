import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import uuid

class VehicleRentalSystem:
    def __init__(self, db_name: str = "rental_system.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                license_number TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Vehicles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id TEXT PRIMARY KEY,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                license_plate TEXT UNIQUE NOT NULL,
                mileage INTEGER DEFAULT 0,
                daily_rate REAL NOT NULL,
                status TEXT DEFAULT 'available',  -- available, rented, maintenance
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Rentals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rentals (
                rental_id TEXT PRIMARY KEY,
                customer_id TEXT,
                vehicle_id TEXT,
                rental_date DATE NOT NULL,
                return_date DATE,
                actual_return_date DATE,
                rental_cost REAL,
                status TEXT DEFAULT 'active',  -- active, completed, overdue
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
                FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_customer(self, name: str, email: str, phone: str, license_number: str) -> str:
        """Add a new customer"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        customer_id = str(uuid.uuid4())[:8]
        
        cursor.execute('''
            INSERT INTO customers (customer_id, name, email, phone, license_number)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, name, email, phone, license_number))
        
        conn.commit()
        conn.close()
        return customer_id
    
    def add_vehicle(self, make: str, model: str, year: int, license_plate: str, daily_rate: float) -> str:
        """Add a new vehicle"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        vehicle_id = str(uuid.uuid4())[:8]
        
        cursor.execute('''
            INSERT INTO vehicles (vehicle_id, make, model, year, license_plate, daily_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (vehicle_id, make, model, year, license_plate, daily_rate))
        
        conn.commit()
        conn.close()
        return vehicle_id
    
    def rent_vehicle(self, customer_id: str, vehicle_id: str, rental_days: int) -> Optional[str]:
        """Rent a vehicle to a customer"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if customer and vehicle exist
        cursor.execute('SELECT * FROM customers WHERE customer_id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return None
        
        cursor.execute('SELECT status FROM vehicles WHERE vehicle_id = ?', (vehicle_id,))
        vehicle = cursor.fetchone()
        if not vehicle or vehicle[0] != 'available':
            conn.close()
            return None
        
        # Create rental
        rental_id = str(uuid.uuid4())[:8]
        rental_date = date.today()
        return_date = rental_date + timedelta(days=rental_days)
        
        cursor.execute('''
            INSERT INTO rentals (rental_id, customer_id, vehicle_id, rental_date, return_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (rental_id, customer_id, vehicle_id, rental_date, return_date))
        
        # Update vehicle status
        cursor.execute('UPDATE vehicles SET status = "rented" WHERE vehicle_id = ?', (vehicle_id,))
        
        conn.commit()
        conn.close()
        return rental_id
    
    def return_vehicle(self, rental_id: str) -> Optional[float]:
        """Return a rented vehicle and calculate final cost"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.rental_date, r.return_date, r.customer_id, r.vehicle_id, v.daily_rate
            FROM rentals r
            JOIN vehicles v ON r.vehicle_id = v.vehicle_id
            WHERE r.rental_id = ? AND r.status = 'active'
        ''', (rental_id,))
        
        rental = cursor.fetchone()
        if not rental:
            conn.close()
            return None
        
        rental_date, expected_return, customer_id, vehicle_id, daily_rate = rental
        actual_return = date.today()
        days_rented = (actual_return - rental_date).days
        total_cost = days_rented * daily_rate
        
        # Update rental
        cursor.execute('''
            UPDATE rentals 
            SET actual_return_date = ?, rental_cost = ?, status = 'completed'
            WHERE rental_id = ?
        ''', (actual_return, total_cost, rental_id))
        
        # Update vehicle status
        cursor.execute('UPDATE vehicles SET status = "available" WHERE vehicle_id = ?', (vehicle_id,))
        
        conn.commit()
        conn.close()
        return total_cost
    
    def get_available_vehicles(self) -> List[Dict]:
        """Get list of available vehicles"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vehicles WHERE status = "available"')
        vehicles = cursor.fetchall()
        conn.close()
        
        return [{
            'vehicle_id': v[0], 'make': v[1], 'model': v[2], 'year': v[3],
            'license_plate': v[4], 'daily_rate': v[6]
        } for v in vehicles]
    
    def get_customer_rentals(self, customer_id: str) -> List[Dict]:
        """Get all rentals for a customer"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, v.make, v.model
            FROM rentals r
            JOIN vehicles v ON r.vehicle_id = v.vehicle_id
            WHERE r.customer_id = ?
            ORDER BY r.rental_date DESC
        ''', (customer_id,))
        rentals = cursor.fetchall()
        conn.close()
        
        return [{
            'rental_id': r[0], 'rental_date': r[3], 'return_date': r[4],
            'actual_return_date': r[5], 'cost': r[6], 'status': r[7],
            'vehicle': f"{r[9]} {r[10]}"
        } for r in rentals]

# Console Interface
def main_menu():
    system = VehicleRentalSystem()
    
    while True:
        print("\n=== Vehicle Rental Management System ===")
        print("1. Add Customer")
        print("2. Add Vehicle")
        print("3. View Available Vehicles")
        print("4. Rent Vehicle")
        print("5. Return Vehicle")
        print("6. View Customer Rentals")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == '1':
            name = input("Customer name: ")
            email = input("Email: ")
            phone = input("Phone: ")
            license = input("Driver's license: ")
            customer_id = system.add_customer(name, email, phone, license)
            print(f"Customer added successfully! ID: {customer_id}")
        
        elif choice == '2':
            make = input("Vehicle make: ")
            model = input("Vehicle model: ")
            year = int(input("Year: "))
            plate = input("License plate: ")
            rate = float(input("Daily rate: "))
            vehicle_id = system.add_vehicle(make, model, year, plate, rate)
            print(f"Vehicle added successfully! ID: {vehicle_id}")
        
        elif choice == '3':
            vehicles = system.get_available_vehicles()
            if vehicles:
                print("\nAvailable Vehicles:")
                for v in vehicles:
                    print(f"ID: {v['vehicle_id']} | {v['year']} {v['make']} {v['model']} "
                          f"({v['license_plate']}) - ${v['daily_rate']}/day")
            else:
                print("No vehicles available!")
        
        elif choice == '4':
            customer_id = input("Customer ID: ")
            print("\nAvailable Vehicles:")
            vehicles = system.get_available_vehicles()
            for i, v in enumerate(vehicles, 1):
                print(f"{i}. {v['year']} {v['make']} {v['model']} (${v['daily_rate']}/day)")
            
            try:
                vehicle_idx = int(input("Select vehicle number: ")) - 1
                vehicle_id = vehicles[vehicle_idx]['vehicle_id']
                days = int(input("Rental days: "))
                rental_id = system.rent_vehicle(customer_id, vehicle_id, days)
                if rental_id:
                    print(f"Vehicle rented successfully! Rental ID: {rental_id}")
                else:
                    print("Rental failed. Check customer/vehicle availability.")
            except (ValueError, IndexError):
                print("Invalid selection!")
        
        elif choice == '5':
            rental_id = input("Rental ID: ")
            cost = system.return_vehicle(rental_id)
            if cost:
                print(f"Vehicle returned! Final cost: ${cost:.2f}")
            else:
                print("Rental not found or already returned!")
        
        elif choice == '6':
            customer_id = input("Customer ID: ")
            rentals = system.get_customer_rentals(customer_id)
            if rentals:
                print(f"\nRentals for Customer {customer_id}:")
                for r in rentals:
                    print(f"ID: {r['rental_id']} | {r['vehicle']} | "
                          f"{r['rental_date']} -> {r['actual_return_date'] or 'Active'} | "
                          f"${r['cost'] or 0:.2f} | {r['status']}")
            else:
                print("No rentals found for this customer.")
        
        elif choice == '7':
            print("Thank you for using Vehicle Rental Management System!")
            break

if __name__ == "__main__":
    from datetime import timedelta  # Add missing import
    main_menu()