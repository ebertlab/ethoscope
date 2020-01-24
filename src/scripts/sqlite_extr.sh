#!bin/bash
sqlite3 -init 64rois.sql results.db '.exit' > results64.csv
sqlite3 -init 32rois.sql results.db '.exit' > results32.csv
