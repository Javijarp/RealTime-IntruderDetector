"""Bounding Box Drawing and Visualization."""


def draw_boxes(frame, detections: list[dict]):
    """
    Draw detection boxes and labels on frame.

    Colors:
        - Person: Blue (255, 50, 50)
        - Dog: Green (50, 220, 50)

    Args:
        frame: Image data (numpy array, BGR)
        detections (list): List of detections with box coordinates

    Returns:
        frame: Annotated image with drawn boxes
    """
    import cv2

    COLORS = {"Person": (255, 50, 50), "Dog": (50, 220, 50)}

    for det in detections:
        color = COLORS.get(det["class"], (200, 200, 200))
        x1, y1, x2, y2 = det["box"]
        conf = det["confidence"]
        label = f'{det["class"]} {conf}'

        # Draw rectangle
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)

        # Draw label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(
            frame, (x1, y1 - th - 4), (x1 + tw + 4, y1), color, -1
        )

        # Draw label text
        cv2.putText(
            frame,
            label,
            (x1 + 2, y1 - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    return frame
