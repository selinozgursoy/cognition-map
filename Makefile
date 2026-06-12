# Convenience targets. `make demo` takes you from nothing to a running app.
.PHONY: install map sleep-edf eegbci api web demo clean

install:
	pip install -r requirements.txt
	cd web && npm install

map:                       ## build a map from synthetic EEG (no download)
	python -m pipeline.run_pipeline --config configs/default.yaml

sleep-edf:                 ## build a map from real Sleep-EDF data (PhysioNet)
	python -m pipeline.run_pipeline --config configs/sleep_edf.yaml

eegbci:                    ## build a map from real Motor Imagery data (PhysioNet)
	python -m pipeline.run_pipeline --config configs/eegbci.yaml

api:
	uvicorn api.main:app --reload --port 8000

web:
	cd web && npm run dev

demo: map
	@echo "Run built. Now start the API (make api) and the frontend (make web)."

clean:
	rm -rf artifacts/*/ web/node_modules web/dist
