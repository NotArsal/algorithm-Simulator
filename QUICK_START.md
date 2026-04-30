# Quick Start Guide

## 🚀 Start the Server

### Option 1: Using Batch File (Easiest)
Double-click: `START_SERVER.bat`

### Option 2: Manual Start
```bash
cd server
python app.py
```

## 🌐 Access the Application

Once the server starts, open your browser and go to:
**http://localhost:5000**

## 📋 What You Can Do

### Current Features (Available Now)
- ✅ **Pune Road Network** - 32,000+ nodes
- ✅ **Mountain Locations** - Connected to road network
- ✅ **Rural Locations** - Connected to road network
- ✅ **Energy Calculations** - For drones and ground bots
- ✅ **Battery Feasibility** - Round trip checking
- ✅ **Travel Time** - Estimated travel times

### Coming Soon (Download in Progress)
- ⏳ **Full India Road Network** - 30 major cities
- ⏳ **Extended Coverage** - More locations across India

## 🔋 Using the System

1. **Select Start Location** - Choose from dropdown (Mountain/Rural/Pune)
2. **Select End Location** - Choose destination
3. **Choose Vehicle Type**:
   - **Drone** - Direct paths, faster
   - **Ground Bot** - Road-based routing
4. **Enter Battery Capacity** - In Watt-hours (Wh)
5. **Click "Compute Route"**

## 📊 What You'll See

- **Route on Map** - Visual route display
- **Distance** - One-way and round trip
- **Travel Time** - Estimated hours/minutes
- **Energy Consumption** - Wh required
- **Battery Requirement** - Minimum battery needed
- **Feasibility Status** - ✅ Feasible or ❌ Not Feasible

## 🔍 Check India Download Status

```bash
python check_download_status.py
```

When complete, the server will automatically use the India data!

## ⚠️ Troubleshooting

### Server won't start?
- Check if port 5000 is available
- Make sure Python is installed
- Install Flask: `pip install flask`

### Routes not found?
- Make sure `navigation.exe` exists
- Check that CSV files are in `data/` folder

### Download issues?
- Check internet connection
- Verify D: drive has space
- Check `D:\navigation_india_osm\` folder

---

**Ready to go!** Start the server and begin planning energy-efficient routes! 🚁🤖

