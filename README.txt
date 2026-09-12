MARITIME CRUISE PLANNER
========================

A Streamlit application for planning multi-leg maritime voyages, estimating
fuel requirements and costs, scheduling port stays, and generating training
watchbills.

FEATURES
--------
- Route planning between supported maritime ports.
- Multiple stopovers and port-of-call sequencing.
- Return routes by selecting the origin as the final destination.
- Distance and true-course calculations for every leg.
- Transit duration and final ETA calculations.
- Flexible ETD date and time planning.
- NATO maritime time zones, including Zulu, Bravo, and Charlie.
- Independent departure date, time, and time zone for each stopover.
- Stay duration in whole days at each stopover.
- Target ETA planning by specific date/time or whole voyage days.
- Automatic average-speed calculation for target schedules.
- Manual course-change waypoints for planning around hazards or land masses.
- Fuel consumption, reserve, and total cost estimates.
- Fuel prices and costs displayed in US dollars (USD).
- Interactive route map and leg-by-leg voyage summary.
- Training roster and four-hour watchbill generation.
- Downloadable watchbill CSV output.

REQUIREMENTS
------------
- Python 3.10 or newer recommended.
- Windows PowerShell commands below assume the included .venv folder.

SETUP
-----
1. Open PowerShell in the project directory:

   cd D:\MaritimeCalculator

2. Create a virtual environment if one does not already exist:

   python -m venv .venv

3. Activate the environment:

   .\.venv\Scripts\Activate.ps1

4. Install dependencies:

   python -m pip install -r requirements.txt

RUN THE STREAMLIT APP
---------------------
From the project directory, run:

   .\.venv\Scripts\python.exe -m streamlit run app.py

Then open:

   http://localhost:8501

If port 8501 is busy, use another port:

   .\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502

DEPLOY TO STREAMLIT COMMUNITY CLOUD
-----------------------------------
1. Push this project folder to a GitHub repository. The repository must contain
   app.py, nautical_calc.py, requirements.txt, and the other project files.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Select "Create app" or "New app".
4. Choose the GitHub repository and branch containing this project.
5. Set the main file path to:

   app.py

6. Deploy the app.

The requirements.txt file includes Streamlit, pandas, and pydeck, which are
required by app.py. Do not upload the .venv folder. The included .gitignore
excludes the virtual environment, caches, compiled files, and local secrets.

If deployment fails, open the Streamlit Cloud app logs. An import error usually
means a dependency is missing from requirements.txt or the main file path is
incorrect. For this project the correct main file is app.py.

ROUTE PLANNING
--------------
1. Select the origin port.
2. Select the number of stopovers.
3. Select each port of call in the desired order.
4. Enter stay days for each stopover.
5. Select the final destination. It may be the origin for a return voyage.
6. Set speed, fuel consumption, fuel price in USD/L, and reserve percentage.
7. Set the origin ETD date, time, and maritime time zone.
8. Optionally enable independent departure scheduling for each stopover.
9. Choose either calculated ETA or target ETA planning.
10. Add navigation waypoints on the final leg when the direct line is unsafe;
   verify every waypoint against official nautical charts before sailing.

When independent departure scheduling is enabled, enter the departure date,
time, and time zone for that port. Otherwise, the next departure is calculated
from the port arrival time plus the configured stay duration.

MARITIME TIME ZONES
-------------------
The planner uses NATO maritime zone names with fixed UTC offsets:

- Zulu: UTC+0
- Alpha: UTC+1
- Bravo: UTC+2
- Charlie: UTC+3
- Delta: UTC+4
- Echo: UTC+5
- Foxtrot: UTC+6
- Golf: UTC+7
- Hotel: UTC+8
- India: UTC+9
- Kilo: UTC+10
- Lima: UTC+11
- Mike: UTC+12
- November through Yankee: UTC-1 through UTC-12

TESTING
-------
Run the automated tests with:

   .\.venv\Scripts\python.exe -m pytest -q

Compile the Python files with:

   .\.venv\Scripts\python.exe -m py_compile app.py nautical_calc.py cruise_planner.py skylight_tracker.py test_nautical_calc.py

OTHER ENTRY POINTS
------------------
- cruise_planner.py: launches the same Streamlit planner through app.main().
- nautical_calc.py: includes the command-line nautical calculator.
- skylight_tracker.py: optional Skylight AIS portal; it requires a valid API key
  and is separate from the main cruise planner.

SUPPORTED PORTS
---------------
The main planner includes ports in Kenya, Tanzania, Seychelles, Madagascar,
Somalia, Comoros, and Mauritius, including Mombasa, Shimoni, Dar es Salaam,
Zanzibar, Port Victoria, Diego Suarez, Toamasina, Mogadishu, Kismayo, Bosaso,
Berbera, Marka (Merca), Eyl, Lamu, Malindi, Tanga, Pemba Island, Moroni, and
Port Louis.

IMPORTANT NOTES
---------------
- Fuel price is treated as US dollars per litre (USD/L).
- Fuel consumption applies to sailing time; time spent stopped in port does not
  consume voyage fuel in the current model.
- Target ETA planning calculates an average speed for the sailing distance.
- Navigation waypoints are planning aids, not certified collision avoidance or
   chart data. Always validate routes against current official nautical charts,
   notices to mariners, depth information, traffic, weather, and local rules.
- Port coordinates and time zones are stored in app.py and nautical_calc.py.
