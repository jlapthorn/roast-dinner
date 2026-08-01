# Roast Dinner

A small Flask web app that builds a reverse cooking timetable for a roast dinner.

Pick when you want to eat, choose meats (with weight in kg), vegetables, and Yorkshire puddings, and the app works backwards from serve time using fan-assisted oven timings.

## Features

- Meal planner with date/time and food selection
- Meat cooking times from weight (kg), fan oven temperature, plus rest time
- Fixed cook times for vegetables and Yorkshire puddings (no oven temperature required)
- Create, edit, and delete foods (SQLite)
- Responsive layout for phone and desktop
- Save the cooking plan as a PDF
- OpenShift Helm chart with SQLite on a PVC

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Optional: set `DATA_DIR` to choose where `roast_dinner.db` is written (defaults to `./instance`).

## Default foods

Seeded on first run (all editable):

| Food | Category | Timing |
|------|----------|--------|
| Chicken, Beef (medium), Pork, Lamb | Meat | Weight-based + fan °C |
| Carrots, Peas, Tenderstem broccoli, Broccoli | Vegetable | Fixed time |
| Yorkshire puddings | Other | Fixed time |

Timings are typical home-cooking guidance — adjust them under **Foods** to match how you cook.

## OpenShift (Helm)

The chart under `charts/roast-dinner` deploys:

- Deployment (1 replica, `Recreate` strategy — required for RWO + SQLite)
- Service + OpenShift Route
- PVC mounted at `/data` (`DATA_DIR`) for persistent SQLite
- Secret for `SECRET_KEY`

### 1. Build into the OpenShift internal registry

```bash
oc new-project roast-dinner
oc new-build --name=roast-dinner --binary --strategy=docker -n roast-dinner
oc start-build roast-dinner --from-dir=. --follow -n roast-dinner
```

### 2. Install the chart

```bash
helm upgrade --install roast-dinner ./charts/roast-dinner \
  --namespace roast-dinner \
  --set image.repository=image-registry.openshift-image-registry.svc:5000/roast-dinner/roast-dinner \
  --set image.tag=latest \
  --set image.pullPolicy=Always \
  --set persistence.storageClass=lvms-vg1
```

### 3. Open the route

```bash
oc get route roast-dinner -n roast-dinner -o jsonpath='https://{.spec.host}{"\n"}'
```

### Useful values

| Value | Default | Notes |
|-------|---------|--------|
| `persistence.size` | `1Gi` | SQLite PVC size |
| `persistence.storageClass` | `""` | Cluster default if empty |
| `persistence.existingClaim` | `""` | Use an existing PVC instead |
| `persistence.mountPath` | `/data` | Must match `DATA_DIR` |
| `route.host` | `""` | Auto-generated if empty |
| `replicaCount` | `1` | Keep at 1 for SQLite |

Example with a named storage class:

```bash
helm upgrade --install roast-dinner ./charts/roast-dinner \
  --namespace roast-dinner \
  --set persistence.storageClass=gp3-csi \
  --set image.tag=latest
```
