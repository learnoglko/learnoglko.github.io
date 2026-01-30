import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 두 벡터 정의
u = np.array([1, 1, 0])
v = np.array([0, 1, 1])

# 외적 계산
w = np.cross(u, v)

# 원점
origin = np.array([0, 0, 0])

# 인터랙티브 3D 시각화
fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection='3d')

# 벡터 그리기
ax.quiver(*origin, *u, color='r', label='u', linewidth=2, arrow_length_ratio=0.1)
ax.quiver(*origin, *v, color='g', label='v', linewidth=2, arrow_length_ratio=0.1)
ax.quiver(*origin, *w, color='b', label='u x v', linewidth=2, arrow_length_ratio=0.1)

# 평면 시각화 (u와 v가 만드는 평면)
plane_x, plane_y = np.meshgrid(np.linspace(0,1.5,2), np.linspace(0,1.5,2))
# u, v 평면 근사
plane_z = 0.5*plane_x + 0.5*plane_y  # 단순화된 평면 예시
ax.plot_surface(plane_x, plane_y, plane_z, color='y', alpha=0.2)

# 축 설정
ax.set_xlim([0,2])
ax.set_ylim([0,2])
ax.set_zlim([0,2])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('벡터 u, v와 외적 u x v (회전 가능)')
ax.legend()
ax.view_init(elev=20., azim=30)  # 초기 시점
plt.tight_layout()
plt.show()
