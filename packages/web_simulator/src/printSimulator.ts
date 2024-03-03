export class PrintSimulator {
    interrupted: boolean = true;


    targetTemps: { "heater_bed": number, "hotend": number };
    setHeater: (heater: string, temp: number) => void;
    setProgress: (pct: number) => void;
    setStatus: (status: string) => void;


    constructor(targetTemps: { "heater_bed": number, "hotend": number }, setHeater: (heater: string, temp: number) => void, setProgress: (pct: number) => void,
        setStatus: (status: string) => void) {
        this.targetTemps = targetTemps;
        this.setHeater = setHeater;
        this.setProgress = setProgress;
        this.setStatus = setStatus;

    }

    async run() {
        let phases = this._generatePhases()
        this.interrupted = false;
        for (let phase of phases) {
            for (let step of phase) {
                if (this.interrupted) return;
                await step()
            }
        }
    }

    _generatePhases() {
        const _this = this;
        return [
            fixed([
                () => {
                    _this.setStatus("idle")
                    return Promise.resolve();
                },
                delay(2000)
            ]),
            (function* () {
                _this.setStatus("Heating bed");
                for (let i = 0; i <= _this.targetTemps.heater_bed; i++) {
                    _this.setHeater("heater_bed", i);
                    yield delay(100);
                }
            })(),
            (function* () {
                _this.setStatus("Heating hotend");
                for (let i = 0; i <= _this.targetTemps.hotend; i++) {
                    _this.setHeater("hotend", i);
                    yield delay(50);
                }
            })(),
            (function* () {
                _this.setStatus("Printing");
                for (let i = 0; i <= 100; i++) {
                    _this.setProgress(i);
                    yield delay(100);
                }
                _this.setStatus("Finished");
            })()
        ];
    }

    stop() {
        this.interrupted = true;
    }
}

const delay = (ms: number) => async () => new Promise(resolve => window.setTimeout(resolve, ms));

function* fixed(col: (() => Promise<unknown>)[]): Generator<() => Promise<unknown>, void, unknown> {
    for (let c of col) yield c;
}

