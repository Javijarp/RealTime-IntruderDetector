"""Entry Point for Edge Module Application."""

from config import Config
from edge_module import EdgeModule
from shared import log


def print_header():
    """Print startup information."""
    modo_texto = (
        "LIVE (cámara real + ventana)"
        if Config.LIVE_MODE
        else "SIMULACIÓN (sin cámara ni red)"
    )

    print("=" * 70)
    print("  MÓDULO EDGE — Sistema de Seguridad con Detección en Tiempo Real")
    print(f"  Modo: {modo_texto}")
    print("=" * 70)
    print()
    print("  Config actual:")
    print(f"    • Modo                  : {'LIVE' if Config.LIVE_MODE else 'SIMULADO'}")
    print(
        f"    • FPS                   : {int(1 / Config.FRAME_INTERVAL_S)} "
        f"{'(simulado)' if not Config.LIVE_MODE else '(cámara real)'}"
    )
    print(f"    • Deadline intruso      : {Config.DEADLINE_INTRUSO_MS} ms")
    print(f"    • Cooldown por entidad  : {Config.COOLDOWN_S} s")
    print(f"    • Buffer máximo         : {Config.BUFFER_MAX} eventos")
    print(f"    • Fallo de red simulado : {Config.SIMULATE_NETWORK_FAILURE}")
    print(f"    • Backend URL (sim)     : {Config.BACKEND_URL}")
    print()

    if Config.LIVE_MODE:
        print("  LIVE: Se abrirá una ventana con la cámara.")
        print("        Azul  = Person | Verde = Dog")
        print("        Presiona 'q' en la ventana para cerrarla.")
    else:
        print("  SIMULADO: No se abre cámara ni ventana.")
        print("  TIPs:")
        print("    • Para ver la cámara real, cambia Config.LIVE_MODE = True")
        print("      (requiere: pip install opencv-python ultralytics)")
        print("    • Para ver el buffer en acción, cambia")
        print("      Config.SIMULATE_NETWORK_FAILURE = True")

    print("=" * 70)
    print()


def main():
    """Main entry point."""
    print_header()

    edge = EdgeModule()
    threads = edge.start()

    log("[MAIN  ] Sistema iniciado. Esperando datos de cámara…")
    print()
    print("  Ventana abierta. Presiona 'q' para cerrar.")
    print()

    try:
        if Config.LIVE_MODE:
            edge.display_frame_mainthread()
        else:
            # Simulation mode: just wait
            while True:
                try:
                    import time
                    time.sleep(1)
                except KeyboardInterrupt:
                    raise
    except KeyboardInterrupt:
        print()
        log("[MAIN  ] Ctrl+C recibido.")
    except Exception as e:
        log(f"[MAIN  ] Error: {e}")
    finally:
        log("[MAIN  ] Señal de parada. Cerrando hilos…")
        edge.stop()
        for t in threads:
            t.join(timeout=3)
        log("[MAIN  ] Sistema Edge apagado limpiamente.")


if __name__ == "__main__":
    main()
