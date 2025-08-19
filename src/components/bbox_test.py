import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

class BoundingBox:
    def __init__(self, p1, p2):
        # ensure p1 is the min corner and p2 is the max corner
        self.p1 = np.minimum(p1, p2)
        self.p2 = np.maximum(p1, p2)

    def corners(self):
        """Return the 8 corners of the bounding box."""
        x1, y1, z1 = self.p1
        x2, y2, z2 = self.p2
        return np.array([
            [x1, y1, z1],
            [x1, y1, z2],
            [x1, y2, z1],
            [x1, y2, z2],
            [x2, y1, z1],
            [x2, y1, z2],
            [x2, y2, z1],
            [x2, y2, z2]
        ])

    @staticmethod
    def enclosing(B1, B2):
        p1 = np.minimum(B1.p1, B2.p1)
        p2 = np.maximum(B1.p2, B2.p2)
        return BoundingBox(p1, p2)

def draw_bbox(ax, bbox, color="blue", alpha=0.15):
    corners = bbox.corners()
    faces = [
        [corners[j] for j in [0,1,3,2]],
        [corners[j] for j in [4,5,7,6]],
        [corners[j] for j in [0,1,5,4]],
        [corners[j] for j in [2,3,7,6]],
        [corners[j] for j in [0,2,6,4]],
        [corners[j] for j in [1,3,7,5]]
    ]
    ax.add_collection3d(Poly3DCollection(faces, facecolors=color, linewidths=1, edgecolors="k", alpha=alpha))

# Example bounding boxes
B1 = BoundingBox(np.array([0, 0, 0]), np.array([1, 2, 3]))
B2 = BoundingBox(np.array([2, 1, 1]), np.array([4, 3, 2]))
B3 = BoundingBox.enclosing(B1, B2)

# Plot
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

draw_bbox(ax, B1, color="red", alpha=0.3)
draw_bbox(ax, B2, color="green", alpha=0.3)
draw_bbox(ax, B3, color="blue", alpha=0.15)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Bounding Boxes B1 (red), B2 (green), B3 enclosing (blue)")

plt.show()
