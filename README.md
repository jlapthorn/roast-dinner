# Roast Dinner

A small Flask web app that builds a reverse cooking timetable for a roast dinner.

Pick when you want to eat, choose meats (with weight in kg), vegetables, and Yorkshire puddings, and the app works backwards from serve time using fan-assisted oven timings.

## Features

- Meal planner with date/time and food selection
- Meat cooking times from weight (kg), plus rest time
- Fixed times for vegetables and Yorkshire puddings
- Create, edit, and delete foods (SQLite)
- Responsive layout for phone and desktop

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Default foods

Seeded on first run (all editable):

| Food | Category | Fan oven |
|------|----------|----------|
| Chicken, Beef (medium), Pork, Lamb | Meat | Weight-based |
| Carrots, Peas, Tenderstem broccoli, Broccoli | Vegetable | Fixed time |
| Yorkshire puddings | Other | Fixed time |

Timings are typical home-cooking guidance — adjust them under **Foods** to match how you cook.
