import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
import led_effect  # noqa: E402


class _DummyPrinter:
    @staticmethod
    def config_error(message):
        return RuntimeError(message)


class _DummyHandler:
    name = "test"
    printer = _DummyPrinter()


class LayerChaseTest(unittest.TestCase):
    def _new_layer(self, cutoff):
        return led_effect.ledEffect.layerChase(
            handler=_DummyHandler(),
            frameHandler=None,
            ledCount=4,
            paletteColors=[0.1, 1, 0.1, 0.1],
            effectRate=3,
            effectCutoff=cutoff,
            frameRate=1 / 24.0,
            blendingMode="top",
        )

    def test_rejects_non_positive_cutoff(self):
        with self.assertRaisesRegex(RuntimeError, "effect cutoff for chase must be > 0"):
            self._new_layer(0)

    def test_accepts_positive_cutoff(self):
        layer = self._new_layer(0.1)
        self.assertGreater(layer.frameCount, 0)


if __name__ == "__main__":
    unittest.main()
