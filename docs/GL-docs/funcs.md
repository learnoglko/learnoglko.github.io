## glEnable
glEnable 함수를 사용하면 OpenGL에 대한 여러 상태 옵션이나 기능을 설정할 수 있습니다. 기능이 활성화되면 glDisable을 통해 비활성화 할 때까지 활성화 상태를 유지합니다.

glEnable의 인자는 다음과 같습니다.

 - cap: GL 기능을 나타내는 상수입니다.

사용 예:

```cpp
glEnable(GL_DEPTH_TEST);
```