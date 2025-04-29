
# 🏋️‍♂️ Fitness Member Management System
Fitness Member Management System — A complete gym management solution built with **Flask**, **MongoDB**, and **HTML/CSS**, implementing **OOP concepts** and **data structures** (Queue, Heap) to manage **members**, **check-ins**, **payments**, **equipment scheduling**, and more efficiently! 🚀

![image](https://github.com/user-attachments/assets/9659cdaf-cb12-4226-9373-725d861224af)

## 📁 Repository Structure
There are **5 files/folders** in the repo:
- **1 - templates** 🧩: Contains the HTML pages of our application.
- **2 - static** 🎨: Contains `style.css` and images for the UI of our application.
- **3 - app.py** 🐍: Main Python code for our Fitness Member Management System.
- **4 - requirements.txt** 📜: Lists the required Python packages for the project.

![image](https://github.com/user-attachments/assets/38e77334-f7d8-4c6f-8d2b-d4747643f3a0)

## ⚙️ Setup Instructions

### Step 1️⃣: Set Up MongoDB Database
Create a database in MongoDB and run the following code in the MongoDB shell:

```javascript
db.admins.insertOne({
  name: "Admin User",
  email: "admin@example.com",
  password: "admin123"
})

db.members.insertOne({
  name: "John Doe",
  email: "john@example.com",
  phone: "1234567890",
  password: "password123"
})

db.workouts.insertOne({
  member_email: "john@example.com",
  schedule: "Mon-Wed-Fri",
  notes: "Chest and arms"
})

db.diets.insertOne({
  member_email: "john@example.com",
  plan: "High protein, low carb"
})

db.payments.insertOne({
  member_id: "1",
  amount: 1000,
  payment_date: "2025-04-16",
  membership_type: "Monthly"
})

db.emergency_contacts.insertOne({
  member_id: "1",
  contact_name: "Jane Doe",
  contact_number: "9876543210"
})

db.feedback.insertOne({
  member_id: "1",
  feedback: "Great gym!",
  timestamp: new Date()
})

db.equipment.insertOne({
  name: "Treadmill",
  quantity: 5,
  condition: "Good",
  added_date: new Date()
})

db.equipment_schedule.insertOne({
  equipment_id: "1",
  time_slot: "9:00 AM - 10:00 AM"
})

db.attendance.insertOne({
  member_id: "1",
  date: "2025-04-16",
  status: "Present"
})

db.checkins.insertOne({
  member_id: "1",
  timestamp: new Date()
})

db.checkouts.insertOne({
  member_id: "1",
  timestamp: new Date()
})
```

### Step 2️⃣: Update Connection String
Copy your **MongoDB connection string** and update it inside `app.py`. 🔗

### Step 3️⃣: Run the Application
- Execute `app.py` 💻
- Click on the HTTP link shown in the terminal.
- You’ll be directed to the **UI page**. 🌐

![image](https://github.com/user-attachments/assets/4a1116e4-806f-4a57-9045-043a64aebb65)
![image](https://github.com/user-attachments/assets/ed0f7c20-d6b2-4f35-ae25-c244befdcb9a)

---

## 🔑 Admin Credentials
- **User ID**: `admin@example.com`
- **Password**: `admin123`

---

## 🎯 Explore the Features of Our Application! 😁

![image](https://github.com/user-attachments/assets/0d163f37-7981-4712-a33f-5fa558b4f3f7)
![image](https://github.com/user-attachments/assets/2c542dd4-ee35-4f46-8304-1df701014bcd)

