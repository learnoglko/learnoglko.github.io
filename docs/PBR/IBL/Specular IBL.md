이 번역본은 번역기를 이용하지 않았으며, https://github.com/rockbenben/md-translator 를 사용하여 번역되었으며, 검수가 전혀 진행되지 않았고, 인간의 손을 거치지 않았습니다. 오직 제가 읽기 위해서 만든 페이지입니다.

# LearnOpenGL - Specular IBL
그 안에서 [이전의](https://learnopengl.com/PBR/IBL/Diffuse-irradiance) 이전 장에서는 PBR을 이미지 기반 조명과 결합하여 조명의 간접 확산 부분으로 사용될 조도 맵을 미리 계산하는 방법을 살펴보았습니다. 이번 장에서는 반사율 방정식의 정반사 부분에 초점을 맞추겠습니다.

\\\[ L\_o(p,\\omega\_o) = \\int\\limits\_{\\Omega} (k\_d\\frac{c}{\\pi} + k\_s\\frac{DFG}{4(\\omega\_o \\cdot n)(\\omega\_i \\cdot n)}) L\_i(p,\\omega\_i) n \\cdot \\omega\_i d\\omega\_i \\\]

쿡-토랜스 반사광 부분(kS를 곱한 값)은 적분 전체에 걸쳐 일정하지 않고 입사광 방향뿐만 아니라 입사 시점 방향에도 의존한다는 것을 알 수 있습니다. 모든 입사광 방향과 모든 가능한 시점 방향을 고려하여 적분을 계산하는 것은 조합론적으로 과부하를 초래하고 실시간 계산에는 너무 많은 비용이 소요됩니다. 에픽 게임즈는 몇 가지 타협점을 감수하고 반사광 부분을 미리 컨볼루션하여 실시간으로 처리하는 분할 합 근사법을 제안했습니다.

분할 합 근사법은 반사율 방정식의 반사광 부분을 두 개의 개별 부분으로 분리하여 각각 컨볼루션을 수행한 후, PBR 셰이더에서 반사광 간접 이미지 기반 조명을 위해 다시 결합합니다. 조도 맵을 사전 컨볼루션했던 방식과 유사하게, 분할 합 근사법은 컨볼루션 입력으로 HDR 환경 맵을 필요로 합니다. 분할 합 근사법을 이해하기 위해 반사율 방정식을 다시 살펴보되, 이번에는 반사광 부분에 초점을 맞추겠습니다.

\\\[ L\_o(p,\\omega\_o) = \\int\\limits\_{\\Omega} (k\_s\\frac{DFG}{4(\\omega\_o \\cdot n)(\\omega\_i \\cdot n)} L\_i(p,\\omega\_i) n \\cdot \\omega\_i d\\omega\_i = \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) L\_i(p,\\omega\_i) n \\cdot \\omega\_i d\\omega\_i \\\]

조도 컨볼루션과 동일한 (성능) 이유로, 적분의 반사광 부분을 실시간으로 계산하여 적절한 성능을 기대할 수는 없습니다. 따라서, 반사광 IBL 맵과 같은 것을 얻기 위해 이 적분을 미리 계산하고, 이 맵을 프래그먼트의 법선 벡터로 샘플링하는 것이 바람직합니다. 하지만 여기서 약간 까다로운 부분이 있습니다. 적분이 \\(\\omega\_i\\)에만 의존하고 상수 확산 반사율 항을 적분에서 제외할 수 있었기 때문에 조도 맵을 미리 계산할 수 있었습니다. 그러나 이번에는 BRDF에서 알 수 있듯이 적분이 \\(\\omega\_i\\) 외에도 더 많은 요소에 의존합니다.

\\\[ f\_r(p, w\_i, w\_o) = \\frac{DFG}{4(\\omega\_o \\cdot n)(\\omega\_i \\cdot n)} \\\]

이 적분은 \\(w\_o\\)에도 의존하는데, 미리 계산된 큐브맵을 두 방향 벡터로 샘플링하는 것은 현실적으로 불가능합니다. 이전 장에서 설명했듯이 위치 \\(p\\)는 여기서는 중요하지 않습니다. \\(\\omega\_i\\)와 \\(\\omega\_o\\)의 모든 가능한 조합에 대해 이 적분을 미리 계산하는 것은 실시간 환경에서는 실용적이지 않습니다.

에픽 게임즈의 분할 합 근사법은 사전 계산을 두 개의 개별 부분으로 나누어 나중에 결합하여 원하는 최종 사전 계산 결과를 얻는 방식으로 문제를 해결합니다. 분할 합 근사법은 반사광 적분을 두 개의 개별 적분으로 나눕니다.

\\\[ L\_o(p,\\omega\_o) = \\int\\limits\_{\\Omega} L\_i(p,\\omega\_i) d\\omega\_i \* \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) n \\cdot \\omega\_i d\\omega\_i \\\]

첫 번째 부분(컨볼루션 처리 후)은 사전 필터링된 환경 맵으로 알려져 있으며, (조도 맵과 유사하게) 미리 계산된 환경 컨볼루션 맵이지만, 이번에는 거칠기를 고려합니다. 거칠기 수준이 높아질수록 환경 맵은 더 분산된 샘플 벡터와 컨볼루션되어 더 흐릿한 반사를 생성합니다. 각 거칠기 수준에 대해 컨볼루션을 수행하면 순차적으로 흐릿해지는 결과가 사전 필터링된 맵의 밉맵 레벨에 저장됩니다. 예를 들어, 5개의 서로 다른 거칠기 값에 대한 사전 컨볼루션 결과를 5개의 밉맵 레벨에 저장하는 사전 필터링된 환경 맵은 다음과 같습니다.

![PBR을 위한 5단계 거칠기 레벨에 걸쳐 사전 합성된 환경 맵](https://learnopengl.com/img/pbr/ibl_prefilter_map.png)

우리는 법선 벡터와 그 산란량을 생성하기 위해 법선 방향과 시점 방향을 입력으로 받는 Cook-Torrance BRDF의 정규 분포 함수(NDF)를 사용합니다. 환경 맵을 컨볼루션할 때 시점 방향을 미리 알 수 없기 때문에, Epic Games는 시점 방향(따라서 반사 방향)이 출력 샘플 방향(ω₀)과 같다고 가정하여 추가적인 근사치를 적용합니다. 이는 다음 코드로 표현됩니다.

```

vec3 N = normalize(w_o);
vec3 R = N;
vec3 V = R;

```


이러한 방식을 사용하면 사전 필터링된 환경 컨볼루션이 시점 방향을 고려할 필요가 없습니다. 하지만 이는 아래 이미지(《Moving Frostbite to PBR》 기사에서 발췌)에서처럼 특정 각도에서 반사면을 볼 때 부드러운 스침 반사 효과를 얻을 수 없다는 것을 의미합니다. 그러나 이는 일반적으로 허용 가능한 절충안으로 간주됩니다.

![V = R = N의 분할합 근사법을 사용하여 스침 반사를 제거합니다.](https://learnopengl.com/img/pbr/ibl_grazing_angles.png)

분할 합 방정식의 두 번째 부분은 반사 적분의 BRDF 부분과 같습니다. 입사광이 모든 방향에서 완전히 흰색이라고 가정하면(즉, \\(L(p, x) = 1.0\\)), 입력 거칠기와 법선 \\(n\\)과 광원 방향 사이의 각도 \\(\\omega\_i\\), 즉 \\(n \\cdot \\omega\_i\\)가 주어졌을 때 BRDF의 응답을 미리 계산할 수 있습니다. Epic Games는 다양한 거칠기 값에 대한 각 법선 및 광원 방향 조합에 대한 미리 계산된 BRDF 응답을 BRDF 적분 맵이라고 하는 2D 룩업 텍스처(LUT)에 저장합니다. 이 2D 룩업 텍스처는 표면의 프레넬 응답에 대한 스케일(빨간색)과 바이어스 값(녹색)을 출력하여 분할 반사 적분의 두 번째 부분을 제공합니다.

![OpenGL에서 PBR에 대한 분할합 근사법에 따른 2D BRDF LUT 시각화.](https://learnopengl.com/img/pbr/ibl_brdf_lut.png)

우리는 수평 텍스처 좌표(범위는 ~ 사이)를 처리하여 조회 텍스처를 생성합니다. `0.0` 그리고 `1.0`평면의 를 BRDF의 입력값인 \\(n \\cdot \\omega\_i\\)로, 수직 텍스처 좌표를 입력 거칠기 값으로 사용합니다. 이 BRDF 적분 맵과 사전 필터링된 환경 맵을 결합하여 반사 적분 결과를 얻을 수 있습니다.

```

float lod             = getMipLevelFromRoughness(roughness);
vec3 prefilteredColor = textureCubeLod(PrefilteredEnvMap, refVec, lod);
vec2 envBRDF          = texture2D(BRDFIntegrationMap, vec2(NdotV, roughness)).xy;
vec3 indirectSpecular = prefilteredColor * (F * envBRDF.x + envBRDF.y) 

```


이를 통해 에픽 게임즈의 분할 합 근사법이 반사율 방정식의 간접 반사 부분을 대략적으로 어떻게 표현하는지 개괄적으로 이해할 수 있을 것입니다. 이제 직접 사전 합성된 부분을 만들어 보겠습니다.

HDR 환경 맵 사전 필터링
------------------------------------

환경 맵을 사전 필터링하는 것은 조도 맵을 컨볼루션하는 방식과 매우 유사합니다. 차이점은 이제 거칠기를 고려하여 사전 필터링된 맵의 밉 레벨에 순차적으로 더 거친 반사를 저장한다는 것입니다.

먼저, 필터링된 환경 맵 데이터를 저장할 새로운 큐브맵을 생성해야 합니다. 필요한 밉 레벨에 충분한 메모리를 할당하기 위해 glGenerateMipmap 함수를 호출하여 필요한 메모리 양을 간편하게 할당합니다.

```

unsigned int prefilterMap;
glGenTextures(1, &prefilterMap);
glBindTexture(GL_TEXTURE_CUBE_MAP, prefilterMap);
for (unsigned int i = 0; i < 6; ++i)
{
    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB16F, 128, 128, 0, GL_RGB, GL_FLOAT, nullptr);
}
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE);
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR); 
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

glGenerateMipmap(GL_TEXTURE_CUBE_MAP);

```


참고로, 프리필터맵의 밉맵을 샘플링할 예정이므로 삼선형 필터링을 활성화하려면 프리필터맵의 축소 필터를 GL_LINEAR_MIPMAP_LINEAR로 설정해야 합니다. 사전 필터링된 반사광은 기본 밉 레벨에서 면별 해상도 128x128로 저장됩니다. 대부분의 반사에는 이 해상도가 충분하지만, 자동차 반사처럼 매끄러운 재질이 많은 경우에는 해상도를 높이는 것이 좋습니다.

이전 장에서는 구면 좌표계를 사용하여 반구 \\(\\Omega\\)에 균일하게 분포된 샘플 벡터를 생성함으로써 환경 맵을 컨볼루션했습니다. 이는 조도에는 잘 작동하지만, 반사에는 효율성이 떨어집니다. 반사의 경우, 표면의 거칠기에 따라 빛은 법선 \\(n\\) 위의 반사 벡터 \\(r\\) 주위로 대략적으로 반사되지만 (표면이 극도로 거칠지 않은 한) 어쨌든 반사 벡터 주위로 반사됩니다.

![PBR 미세면 표면 모델에 따른 반사엽.](https://learnopengl.com/img/pbr/ibl_specular_lobe.png)

반사되는 빛의 일반적인 형태를 반사 로브(specular lobe)라고 합니다. 표면 거칠기가 증가함에 따라 반사 로브의 크기가 커지고, 입사광의 방향에 따라 반사 로브의 모양도 변합니다. 따라서 반사 로브의 모양은 재질에 매우 의존적입니다.

미세 표면 모델에서 반사 로브는 입사광의 방향에 따라 미세면의 중간 벡터를 중심으로 한 반사 방향으로 생각할 수 있습니다. 대부분의 광선이 미세면의 중간 벡터를 중심으로 반사된 반사 로브에 도달하므로, 대부분의 광선이 낭비되는 것을 방지하기 위해 유사한 방식으로 샘플 벡터를 생성하는 것이 합리적입니다. 이러한 과정을 중요도 샘플링이라고 합니다.

### 몬테카를로 적분 및 중요도 샘플링

중요도 표본 추출을 완전히 이해하려면 먼저 몬테카를로 적분이라는 수학적 개념을 살펴보는 것이 중요합니다. 몬테카를로 적분은 주로 통계학과 확률론의 조합으로 이루어집니다. 몬테카를로 적분은 전체 모집단을 고려하지 않고도 모집단의 특정 통계량이나 값을 계산하는 데 도움을 줍니다.

예를 들어, 한 국가 전체 국민의 평균 키를 알고 싶다고 가정해 봅시다. 정확한 답을 얻으려면 **모든** 국민의 키를 측정하고 평균을 내면 됩니다. 하지만 대부분의 국가는 인구가 상당히 많기 때문에 이는 현실적인 방법이 아닙니다. 너무 많은 노력과 시간이 소요될 것입니다.

다른 방법은 이 모집단에서 훨씬 작은 **완전히 무작위적인**(편향되지 않은) 부분집합을 추출하여 키를 측정하고 평균을 내는 것입니다. 이 모집단의 크기는 100명 정도로 작을 수 있습니다. 정확한 값만큼 정밀하지는 않지만, 실제 값에 비교적 가까운 결과를 얻을 수 있습니다. 이를 대수의 법칙이라고 합니다. 전체 모집단에서 크기가 N인 작은 표본을 추출하여 키를 측정하면, 그 결과는 실제 값에 비교적 가깝고, 표본의 개수(N)가 증가할수록 실제 값에 더 가까워진다는 것입니다.

몬테카를로 적분은 대수의 법칙을 기반으로 하며 적분을 푸는 데 동일한 접근 방식을 취합니다. 모든 가능한 (이론적으로 무한한) 표본 값 \\(x\\)에 대해 적분을 푸는 대신, 전체 모집단에서 무작위로 추출한 \\(N\\)개의 표본 값을 생성하고 평균을 냅니다. \\(N\\)이 증가함에 따라 적분의 정확한 해에 더 가까운 결과를 얻을 수 있습니다.

\\\[ O = \\int\\limits\_{a}^{b} f(x) dx = \\frac{1}{N} \\sum\_{i=0}^{N-1} \\frac{f(x)}{pdf(x)} \\\]

적분을 풀기 위해 모집단 \\(a\\)부터 \\(b\\)까지에서 \\(N\\)개의 무작위 표본을 추출하고, 이들을 모두 더한 다음 전체 표본 수로 나누어 평균을 구합니다. \\(pdf\\)는 확률 밀도 함수를 나타내며, 전체 표본 집합에서 특정 표본이 나타날 확률을 보여줍니다. 예를 들어, 모집단의 키에 대한 확률 밀도 함수는 다음과 같습니다.

![확률 분포 함수(PDF) 예시.](https://learnopengl.com/img/pbr/ibl_pdf.png)

이 그래프를 보면, 인구 집단에서 임의로 표본을 추출할 때 키가 1.70인 사람을 표본으로 뽑을 확률이 키가 1.50인 사람을 표본으로 뽑을 확률보다 높다는 것을 알 수 있습니다.

몬테카를로 적분에서 일부 샘플은 다른 샘플보다 생성될 확률이 더 높을 수 있습니다. 이것이 바로 일반적인 몬테카를로 추정에서 샘플링된 값을 확률 밀도 함수(pdf)에 따른 샘플 확률로 나누거나 곱하는 이유입니다. 지금까지 우리가 다룬 각 적분 추정 사례에서 생성된 샘플은 생성될 확률이 모두 동일한 균일 분포를 따랐습니다. 따라서 지금까지의 추정은 편향되지 않았으며, 샘플 수가 계속 증가함에 따라 결국 적분의 **정확한** 해에 수렴하게 됩니다.

하지만 일부 몬테카를로 추정기는 편향되어 있습니다. 즉, 생성된 샘플이 완전히 무작위가 아니라 특정 값이나 방향으로 치우쳐 있다는 뜻입니다. 이러한 편향된 몬테카를로 추정기는 수렴 속도가 빠르다는 장점이 있지만, 편향된 특성 때문에 정확한 해에 수렴하지 못할 가능성이 높습니다. 특히 컴퓨터 그래픽 분야에서는 결과가 시각적으로 만족스럽기만 하면 정확한 해가 그다지 중요하지 않기 때문에 이러한 절충안은 일반적으로 허용됩니다. 곧 살펴보겠지만, 중요도 샘플링(편향된 추정기를 사용함)에서도 생성된 샘플은 특정 방향으로 편향되어 있는데, 이 경우 각 샘플에 해당 확률 밀도 함수(pdf)를 곱하거나 나누어 이러한 편향을 보정합니다.

몬테카를로 적분은 연속 적분을 이산적이고 효율적인 방식으로 근사화하는 직관적인 방법이기 때문에 컴퓨터 그래픽에서 매우 널리 사용됩니다. 샘플링할 영역/부피(예: 반구 \\(\\Omega\\))를 선택하고, 해당 영역/부피 내에서 \\(N\\)개의 무작위 샘플을 생성한 다음, 각 샘플의 기여도를 합산하고 가중치를 부여하여 최종 결과를 계산합니다.

몬테카를로 적분은 광범위한 수학적 주제이므로 자세한 내용은 생략하겠지만, 난수 샘플을 생성하는 방법에는 여러 가지가 있다는 점을 언급하겠습니다. 기본적으로 각 샘플은 우리가 익숙한 것처럼 완전히 (유사)난수이지만, 준난수 시퀀스의 특정 속성을 활용하면 여전히 난수이면서도 흥미로운 특성을 지닌 샘플 벡터를 생성할 수 있습니다. 예를 들어, 저분산 시퀀스(low-discrepancy sequence)라는 것을 사용하여 몬테카를로 적분을 수행할 수 있는데, 이는 여전히 난수 샘플을 생성하지만 각 샘플이 더 고르게 분포되도록 합니다(이미지 제공: James Heald).

![낮은 불일치 시퀀스.](https://learnopengl.com/img/pbr/ibl_low_discrepancy_sequence.png)

몬테카를로 샘플 벡터를 생성할 때 낮은 불일치 시퀀스를 사용하는 경우, 이 과정을 준 몬테카를로 적분이라고 합니다. 준 몬테카를로 방법은 수렴 속도가 빠르기 때문에 성능이 중요한 응용 분야에 적합합니다.

몬테카를로 및 준 몬테카를로 적분에 대한 새롭게 얻은 지식을 바탕으로, 중요도 샘플링이라는 흥미로운 특성을 활용하여 수렴 속도를 더욱 높일 수 있습니다. 이 장에서 이미 언급했듯이, 빛의 정반사에서 반사광 벡터는 표면 거칠기에 의해 크기가 결정되는 정반사 영역(specular lobe) 내에 제한됩니다. 정반사 영역 외부에 있는 (준)무작위로 생성된 샘플은 정반사 적분에 중요하지 않으므로, 몬테카를로 추정기가 편향될 수 있다는 단점이 있지만, 샘플 생성을 정반사 영역 내부에 집중하는 것이 합리적입니다.

이것이 바로 중요도 샘플링의 핵심입니다. 즉, 미세면의 중간 벡터를 중심으로 하는 거칠기 제약 조건 내에서 샘플 벡터를 생성하는 것입니다. 준 몬테카를로 샘플링과 낮은 불일치 시퀀스를 결합하고 중요도 샘플링을 사용하여 샘플 벡터에 편향을 주면 높은 수렴 속도를 얻을 수 있습니다. 해에 더 빨리 도달하기 때문에 충분히 만족스러운 근사치를 얻는 데 필요한 샘플 수가 훨씬 줄어듭니다.

### 낮은 불일치 시퀀스

이 장에서는 준 몬테카를로 방법을 기반으로 하는 무작위 저분산 시퀀스를 사용하여 중요도 샘플링을 통해 간접 반사율 방정식의 정반사 부분을 미리 계산합니다. 우리가 사용할 시퀀스는 해머슬리 시퀀스(Hammersley Sequence)로 알려져 있으며, 이는 다음과 같이 자세히 설명되어 있습니다. [홀거 담머츠](http://holger.dammertz.org/stuff/notes_HammersleyOnHemisphere.html)해머슬리 수열은 십진수 표현을 소수점을 기준으로 이진수 표현과 대칭시키는 반 데르 코르푸트 수열을 기반으로 합니다.

몇 가지 유용한 비트 트릭을 사용하면 셰이더 프로그램에서 Van Der Corput 시퀀스를 상당히 효율적으로 생성할 수 있으며, 이를 사용하여 Hammersley 시퀀스 샘플 i를 얻을 수 있습니다. `N` 총 샘플 수:

```

float RadicalInverse_VdC(uint bits) 
{
    bits = (bits << 16u) | (bits >> 16u);
    bits = ((bits & 0x55555555u) << 1u) | ((bits & 0xAAAAAAAAu) >> 1u);
    bits = ((bits & 0x33333333u) << 2u) | ((bits & 0xCCCCCCCCu) >> 2u);
    bits = ((bits & 0x0F0F0F0Fu) << 4u) | ((bits & 0xF0F0F0F0u) >> 4u);
    bits = ((bits & 0x00FF00FFu) << 8u) | ((bits & 0xFF00FF00u) >> 8u);
    return float(bits) * 2.3283064365386963e-10; // / 0x100000000
}
// ----------------------------------------------------------------------------
vec2 Hammersley(uint i, uint N)
{
    return vec2(float(i)/float(N), RadicalInverse_VdC(i));
}  

```


GLSL Hammersley 함수는 크기가 N인 전체 샘플 세트에서 가장 낮은 불일치를 보이는 샘플 i를 제공합니다.

**비트 연산자 지원이 없는 해머슬리 시퀀스**

모든 OpenGL 관련 드라이버가 비트 연산자를 지원하는 것은 아닙니다(예: WebGL 및 OpenGL ES 2.0). 이러한 경우에는 비트 연산자에 의존하지 않는 Van Der Corput 시퀀스의 다른 버전을 사용하는 것이 좋습니다.

```

float VanDerCorput(uint n, uint base)
{
    float invBase = 1.0 / float(base);
    float denom   = 1.0;
    float result  = 0.0;

    for(uint i = 0u; i < 32u; ++i)
    {
        if(n > 0u)
        {
            denom   = mod(float(n), 2.0);
            result += denom * invBase;
            invBase = invBase / 2.0;
            n       = uint(float(n) / 2.0);
        }
    }

    return result;
}
// ----------------------------------------------------------------------------
vec2 HammersleyNoBitOps(uint i, uint N)
{
    return vec2(float(i)/float(N), VanDerCorput(i, 2u));
}

```


참고로, 구형 하드웨어의 GLSL 루프 제한으로 인해 해당 시퀀스는 가능한 모든 경우를 순회합니다. `32` 비트 연산자를 사용합니다. 이 버전은 성능이 떨어지지만, 비트 연산자가 없는 경우 모든 하드웨어에서 작동합니다.

### GGX 중요도 샘플링

적분 반구(Ω)에 걸쳐 균일하게 또는 무작위로(몬테카를로 방식) 샘플 벡터를 생성하는 대신, 표면 거칠기를 기반으로 미세 표면 중간 벡터의 일반적인 반사 방향에 치우친 샘플 벡터를 생성합니다. 샘플링 과정은 이전에 살펴본 것과 유사합니다. 즉, 큰 루프를 시작하고, 무작위(저분산) 시퀀스 값을 생성하고, 이 시퀀스 값을 사용하여 탄젠트 공간에서 샘플 벡터를 생성하고, 월드 공간으로 변환한 다음, 장면의 복사 휘도를 샘플링합니다. 달라진 점은 이제 저분산 시퀀스 값을 입력으로 사용하여 샘플 벡터를 생성한다는 것입니다.

```

const uint SAMPLE_COUNT = 4096u;
for(uint i = 0u; i < SAMPLE_COUNT; ++i)
{
    vec2 Xi = Hammersley(i, SAMPLE_COUNT);   

```


또한, 샘플 벡터를 생성하기 위해서는 표면 거칠기의 반사광선 영역으로 샘플 벡터를 정렬하고 편향시키는 방법이 필요합니다. 앞서 설명한 NDF를 사용할 수 있습니다. [이론](https://learnopengl.com/PBR/Theory) 에픽 게임즈에서 설명한 대로 구형 샘플 벡터 프로세스에서 GGX NDF를 결합하는 장을 참조하십시오.

```

vec3 ImportanceSampleGGX(vec2 Xi, vec3 N, float roughness)
{
    float a = roughness*roughness;
	
    float phi = 2.0 * PI * Xi.x;
    float cosTheta = sqrt((1.0 - Xi.y) / (1.0 + (a*a - 1.0) * Xi.y));
    float sinTheta = sqrt(1.0 - cosTheta*cosTheta);
	
    // from spherical coordinates to cartesian coordinates
    vec3 H;
    H.x = cos(phi) * sinTheta;
    H.y = sin(phi) * sinTheta;
    H.z = cosTheta;
	
    // from tangent-space vector to world-space sample vector
    vec3 up        = abs(N.z) < 0.999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
    vec3 tangent   = normalize(cross(up, N));
    vec3 bitangent = cross(N, tangent);
	
    vec3 sampleVec = tangent * H.x + bitangent * H.y + N * H.z;
    return normalize(sampleVec);
}  

```


이를 통해 입력된 거칠기 값과 낮은 불일치 시퀀스 값 Xi를 기반으로 예상되는 미세 표면의 중간 벡터를 중심으로 어느 정도 정렬된 샘플 벡터를 얻을 수 있습니다. 참고로, 에픽 게임즈는 디즈니의 PBR 연구를 바탕으로 더 나은 시각적 결과를 위해 거칠기 값을 제곱하여 사용합니다.

저분산 해머슬리 시퀀스와 샘플 생성 방식이 정의되었으므로, 이제 사전 필터 컨볼루션 셰이더를 완성할 수 있습니다.

```

#version 330 core
out vec4 FragColor;
in vec3 localPos;

uniform samplerCube environmentMap;
uniform float roughness;

const float PI = 3.14159265359;

float RadicalInverse_VdC(uint bits);
vec2 Hammersley(uint i, uint N);
vec3 ImportanceSampleGGX(vec2 Xi, vec3 N, float roughness);
  
void main()
{		
    vec3 N = normalize(localPos);    
    vec3 R = N;
    vec3 V = R;

    const uint SAMPLE_COUNT = 1024u;
    float totalWeight = 0.0;   
    vec3 prefilteredColor = vec3(0.0);     
    for(uint i = 0u; i < SAMPLE_COUNT; ++i)
    {
        vec2 Xi = Hammersley(i, SAMPLE_COUNT);
        vec3 H  = ImportanceSampleGGX(Xi, N, roughness);
        vec3 L  = normalize(2.0 * dot(V, H) * H - V);

        float NdotL = max(dot(N, L), 0.0);
        if(NdotL > 0.0)
        {
            prefilteredColor += texture(environmentMap, L).rgb * NdotL;
            totalWeight      += NdotL;
        }
    }
    prefilteredColor = prefilteredColor / totalWeight;

    FragColor = vec4(prefilteredColor, 1.0);
}  
  

```


우리는 사전 필터링 큐브맵의 각 밉맵 레벨에 따라 변하는 입력 거칠기를 기반으로 환경을 사전 필터링합니다. `0.0` 에게 `1.0`그리고 그 결과를 prefilteredColor에 저장합니다. 이렇게 얻은 prefilteredColor 값을 전체 샘플 가중치로 나누는데, 최종 결과에 미치는 영향이 적은 샘플(NdotL 값이 작은 경우)은 최종 가중치에 기여하는 정도가 작습니다.

### 필터 전 밉맵 레벨 캡처

이제 남은 작업은 OpenGL이 여러 밉맵 레벨에 걸쳐 서로 다른 거칠기 값을 사용하여 환경 맵을 미리 필터링하도록 하는 것입니다. 이는 원래 설정값을 사용하면 실제로 상당히 쉽게 구현할 수 있습니다. [조도](https://learnopengl.com/PBR/IBL/Diffuse-irradiance) 장:

```

prefilterShader.use();
prefilterShader.setInt("environmentMap", 0);
prefilterShader.setMat4("projection", captureProjection);
glActiveTexture(GL_TEXTURE0);
glBindTexture(GL_TEXTURE_CUBE_MAP, envCubemap);

glBindFramebuffer(GL_FRAMEBUFFER, captureFBO);
unsigned int maxMipLevels = 5;
for (unsigned int mip = 0; mip < maxMipLevels; ++mip)
{
    // reisze framebuffer according to mip-level size.
    unsigned int mipWidth  = 128 * std::pow(0.5, mip);
    unsigned int mipHeight = 128 * std::pow(0.5, mip);
    glBindRenderbuffer(GL_RENDERBUFFER, captureRBO);
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, mipWidth, mipHeight);
    glViewport(0, 0, mipWidth, mipHeight);

    float roughness = (float)mip / (float)(maxMipLevels - 1);
    prefilterShader.setFloat("roughness", roughness);
    for (unsigned int i = 0; i < 6; ++i)
    {
        prefilterShader.setMat4("view", captureViews[i]);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                               GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, prefilterMap, mip);

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        renderCube();
    }
}
glBindFramebuffer(GL_FRAMEBUFFER, 0);   

```


이 과정은 조도 맵 컨볼루션과 유사하지만, 이번에는 프레임 버퍼의 크기를 적절한 밉맵 크기에 맞춰 조정합니다. 각 밉 레벨은 크기를 2배씩 줄입니다. 또한, glFramebufferTexture2D의 마지막 매개변수에 렌더링할 밉 레벨을 지정하고, 사전 필터링할 거칠기 값을 사전 필터 셰이더에 전달합니다.

이렇게 하면 더 높은 밉 레벨에서 접근할수록 더 흐릿한 반사를 반환하는 적절하게 사전 필터링된 환경 맵을 얻을 수 있습니다. 사전 필터링된 환경 큐브맵을 스카이박스 셰이더에서 사용하고 다음과 같이 첫 번째 밉 레벨보다 약간 높은 레벨에서 강제로 샘플링하면 됩니다.

```

vec3 envColor = textureLod(environmentMap, WorldPos, 1.2).rgb; 

```


결과적으로 원래 환경보다 더 흐릿한 이미지가 나타납니다.

![스카이박스에서 사전 필터링된 환경 맵의 LOD 밉 레벨을 시각화합니다.](https://learnopengl.com/img/pbr/ibl_prefilter_map_sample.png)

비슷하게 보인다면 HDR 환경 맵에 사전 필터링이 성공적으로 적용된 것입니다. 다양한 밉맵 레벨을 조정해 보면서 사전 필터링된 맵이 밉맵 레벨이 높아짐에 따라 선명한 반사에서 흐릿한 반사로 점차 변하는 것을 확인해 보세요.

프리필터 컨볼루션 아티팩트
--------------------------------

현재의 프리필터 맵은 대부분의 용도에 잘 작동하지만, 결국에는 프리필터 컨볼루션과 직접적으로 관련된 몇 가지 렌더링 아티팩트를 접하게 될 것입니다. 여기서는 가장 흔한 아티팩트와 해결 방법을 나열하겠습니다.

### 높은 거칠기에서의 큐브맵 이음새

표면이 거친 표면에서 프리필터 맵을 샘플링한다는 것은 프리필터 맵의 낮은 밉 레벨 중 일부를 샘플링하는 것을 의미합니다. 큐브맵을 샘플링할 때 OpenGL은 기본적으로 큐브맵 면을 가로질러 선형 보간을 수행하지 않습니다. 낮은 밉 레벨은 해상도가 낮고 프리필터 맵이 훨씬 큰 샘플 영역으로 볼록화되기 때문에 큐브 면 사이의 필터링이 부족한 점이 확연히 드러납니다.

![필터 전 맵에서 큐브맵 이음새가 보입니다.](https://learnopengl.com/img/pbr/ibl_prefilter_seams.png)

다행히 OpenGL은 GL_TEXTURE_CUBE_MAP_SEAMLESS를 활성화하여 큐브맵 면 전체에 걸쳐 적절하게 필터링할 수 있는 옵션을 제공합니다.

```

glEnable(GL_TEXTURE_CUBE_MAP_SEAMLESS);  

```


애플리케이션 시작 부분에서 이 속성을 활성화하기만 하면 이음새가 사라집니다.

### 프리필터 컨볼루션의 밝은 점들

반사광에는 높은 주파수 디테일과 매우 다양한 광 강도가 존재하기 때문에, HDR 환경 반사광의 급격한 변화를 제대로 표현하려면 반사광 컨볼루션에 많은 샘플이 필요합니다. 저희는 이미 매우 많은 샘플을 사용하고 있지만, 일부 환경에서는 거친 밉 레벨에서 여전히 샘플 수가 부족할 수 있으며, 이 경우 밝은 영역 주변에 점 패턴이 나타날 수 있습니다.

![프리필터 맵의 더 깊은 밉 LOD 레벨에서 고주파 HDR 맵에 보이는 점들.](https://learnopengl.com/img/pbr/ibl_prefilter_dots.png)

한 가지 방법은 샘플 수를 더 늘리는 것이지만, 모든 환경에 충분하지는 않을 것입니다. 앞서 설명한 바와 같이 [체탄 재그스](https://chetanjags.wordpress.com/2015/08/26/image-based-lighting/) (프리필터 컨볼루션 단계에서) 환경 맵을 직접 샘플링하는 대신, 적분의 PDF와 거칠기를 기반으로 환경 맵의 밉 레벨을 샘플링함으로써 이러한 아티팩트를 줄일 수 있습니다.

```

float D   = DistributionGGX(NdotH, roughness);
float pdf = (D * NdotH / (4.0 * HdotV)) + 0.0001; 

float resolution = 512.0; // resolution of source cubemap (per face)
float saTexel  = 4.0 * PI / (6.0 * resolution * resolution);
float saSample = 1.0 / (float(SAMPLE_COUNT) * pdf + 0.0001);

float mipLevel = roughness == 0.0 ? 0.0 : 0.5 * log2(saSample / saTexel); 

```


샘플링할 밉 레벨을 가져올 환경 맵에서 삼선형 필터링을 활성화하는 것을 잊지 마세요.

```

glBindTexture(GL_TEXTURE_CUBE_MAP, envCubemap);
glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR); 

```


그리고 큐브맵의 기본 텍스처가 설정된 **후**에 OpenGL이 밉맵을 생성하도록 하세요.

```

// convert HDR equirectangular environment map to cubemap equivalent
[...]
// then generate mipmaps
glBindTexture(GL_TEXTURE_CUBE_MAP, envCubemap);
glGenerateMipmap(GL_TEXTURE_CUBE_MAP);

```


이 방법은 놀라울 정도로 효과적이며, 거친 표면에서 사전 필터 맵의 점들을 대부분, 또는 전부 제거해 줄 것입니다.

BRDF 사전 계산
----------------------

사전 필터링된 환경이 준비되었으므로 이제 분할합 근사법의 두 번째 부분인 BRDF에 집중할 수 있습니다. 반사 분할합 근사법을 다시 한번 간단히 살펴보겠습니다.

\\\[ L\_o(p,\\omega\_o) = \\int\\limits\_{\\Omega} L\_i(p,\\omega\_i) d\\omega\_i \* \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) n \\cdot \\omega\_i d\\omega\_i \\\]

우리는 다양한 거칠기 수준에 대한 사전 필터 맵에서 분할 합 근사치의 왼쪽 부분을 미리 계산했습니다. 오른쪽 부분은 각도 \\(n \\cdot \\omega\_o\\), 표면 거칠기 및 프레넬 \\(F\_0\\)에 대한 BRDF 방정식을 합성해야 합니다. 이는 반사 BRDF를 단색 흰색 환경 또는 일정한 복사 휘도 \\(L\_i\\)와 통합하는 것과 유사합니다. `1.0`BRDF를 3개 변수에 대해 합성하는 것은 다소 과하지만, 반사 BRDF 방정식에서 \\(F\_0\\)를 제외하는 방법을 시도해 볼 수 있습니다.

\\\[ \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) n \\cdot \\omega\_i d\\omega\_i = \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) \\frac{F(\\omega\_o, h)}{F(\\omega\_o, h)} n \\cdot \\omega\_i d\\omega\_i \\\]

여기서 \\(F\\)는 프레넬 방정식입니다. 프레넬 방정식의 분모를 BRDF로 옮기면 다음과 같은 동등한 방정식을 얻습니다.

\\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} F(\\omega\_o, h) n \\cdot \\omega\_i d\\omega\_i \\\]

가장 오른쪽의 \\(F\\)를 프레넬-슐릭 근사식으로 대체하면 다음과 같습니다.

\\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (F\_0 + (1 - F\_0){(1 - \\omega\_o \\cdot h)}^5) n \\cdot \\omega\_i d\\omega\_i \\\]

F_0를 더 쉽게 구하기 위해 \\({(1 - \\omega\_o \\cdot h)}^5\\)를 \\(\\alpha\\)로 바꿔 보겠습니다.

\\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (F\_0 + (1 - F\_0)\\alpha) n \\cdot \\omega\_i d\\omega\_i \\\] \\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (F\_0 + 1\*\\alpha - F\_0\*\\alpha) n \\cdot \\omega\_i d\\omega\_i \\\] \\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (F\_0 \* (1 - \\alpha) + \\alpha) n \\cdot \\omega\_i d\\omega\_i \\\]

다음으로 프레넬 함수(F)를 두 개의 적분으로 나눕니다.

\\\[ \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (F\_0 \* (1 - \\alpha)) n \\cdot \\omega\_i d\\omega\_i + \\int\\limits\_{\\Omega} \\frac{f\_r(p, \\omega\_i, \\omega\_o)}{F(\\omega\_o, h)} (\\alpha) n \\cdot \\omega\_i d\\omega\_i \\\]

이렇게 하면 \\(F\_0\\)는 적분 전체에 걸쳐 상수가 되므로 \\(F\_0\\)를 적분 밖으로 꺼낼 수 있습니다. 다음으로 \\(\\alpha\\)를 원래 형태로 다시 대입하면 최종 분할합 BRDF 방정식을 얻습니다.

\\\[ F\_0 \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o)(1 - {(1 - \\omega\_o \\cdot h)}^5) n \\cdot \\omega\_i d\\omega\_i + \\int\\limits\_{\\Omega} f\_r(p, \\omega\_i, \\omega\_o) {(1 - \\omega\_o \\cdot h)}^5 n \\cdot \\omega\_i d\\omega\_i \\\]

결과적으로 얻어진 두 개의 적분은 각각 \\(F\_0\\)에 대한 스케일과 바이어스를 나타냅니다. \\(f\_r(p, \\omega\_i, \\omega\_o)\\)에는 이미 \\(F\\)에 대한 항이 포함되어 있으므로 두 항이 서로 상쇄되어 \\(f\_r\\)에서 \\(F\\)가 제거됩니다.

이전의 복잡한 환경 맵과 유사하게, BRDF 방정식을 입력값인 \\(n\\)과 \\(\\omega\_o\\) 사이의 각도 및 거칠기에 대해 컨볼루션할 수 있습니다. 컨볼루션 결과는 BRDF 통합 맵이라고 하는 2D 룩업 텍스처(LUT)에 저장되며, 이 맵은 나중에 PBR 조명 셰이더에서 최종 컨볼루션된 간접 반사광 결과를 얻는 데 사용됩니다.

BRDF 컨볼루션 셰이더는 2D 평면에서 작동하며, 2D 텍스처 좌표를 BRDF 컨볼루션(NdotV 및 거칠기)의 입력으로 직접 사용합니다. 컨볼루션 코드는 프리필터 컨볼루션과 대체로 유사하지만, 이제 샘플 벡터를 BRDF의 기하 함수와 프레넬-슐릭 근사법에 따라 처리한다는 점이 다릅니다.

```
          
vec2 IntegrateBRDF(float NdotV, float roughness)
{
    vec3 V;
    V.x = sqrt(1.0 - NdotV*NdotV);
    V.y = 0.0;
    V.z = NdotV;

    float A = 0.0;
    float B = 0.0;

    vec3 N = vec3(0.0, 0.0, 1.0);

    const uint SAMPLE_COUNT = 1024u;
    for(uint i = 0u; i < SAMPLE_COUNT; ++i)
    {
        vec2 Xi = Hammersley(i, SAMPLE_COUNT);
        vec3 H  = ImportanceSampleGGX(Xi, N, roughness);
        vec3 L  = normalize(2.0 * dot(V, H) * H - V);

        float NdotL = max(L.z, 0.0);
        float NdotH = max(H.z, 0.0);
        float VdotH = max(dot(V, H), 0.0);

        if(NdotL > 0.0)
        {
            float G = GeometrySmith(N, V, L, roughness);
            float G_Vis = (G * VdotH) / (NdotH * NdotV);
            float Fc = pow(1.0 - VdotH, 5.0);

            A += (1.0 - Fc) * G_Vis;
            B += Fc * G_Vis;
        }
    }
    A /= float(SAMPLE_COUNT);
    B /= float(SAMPLE_COUNT);
    return vec2(A, B);
}
// ----------------------------------------------------------------------------
void main() 
{
    vec2 integratedBRDF = IntegrateBRDF(TexCoords.x, TexCoords.y);
    FragColor = integratedBRDF;
}

```


보시다시피, BRDF 컨볼루션은 수학적 개념을 코드로 직접 변환한 것입니다. 각도 θ와 표면 거칠기를 입력으로 받아 중요도 샘플링을 통해 샘플 벡터를 생성하고, 이를 기하학적 구조와 BRDF에서 파생된 프레넬 항에 적용하여 처리합니다. 마지막으로 각 샘플에 대해 스케일과 F₀ 편향 값을 출력하고, 최종적으로 이들을 평균화합니다.

여러분은 아마도 기억하실 겁니다. [이론](https://learnopengl.com/PBR/Theory) BRDF의 기하학적 항은 IBL과 함께 사용할 때 약간 다르며, 그 이유는 해당 변수 \\(k\\)의 해석이 약간 다르기 때문입니다.

\\\[ k\_{direct} = \\frac{(\\alpha + 1)^2}{8} \\\] \\\[ k\_{IBL} = \\frac{\\alpha^2}{2} \\\]

BRDF 컨볼루션은 반사 IBL 적분의 일부이므로 Schlick-GGX 기하 함수에 \\(k\_{IBL}\\)을 사용하겠습니다.

```

float GeometrySchlickGGX(float NdotV, float roughness)
{
    float a = roughness;
    float k = (a * a) / 2.0;

    float nom   = NdotV;
    float denom = NdotV * (1.0 - k) + k;

    return nom / denom;
}
// ----------------------------------------------------------------------------
float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);

    return ggx1 * ggx2;
}  

```


참고로, (k) 함수는 a를 매개변수로 받지만, 원래 다른 a 해석에서처럼 거칠기를 a로 제곱하지 않았습니다. 아마도 여기서 a가 이미 제곱되어 있기 때문일 것입니다. 이것이 에픽 게임즈의 오류인지 아니면 원래 디즈니 논문의 오류인지는 확실하지 않지만, 거칠기를 a로 직접 변환하면 에픽 게임즈 버전과 동일한 BRDF 적분 맵이 생성됩니다.

마지막으로, BRDF 컨볼루션 결과를 저장하기 위해 512x512 해상도의 2D 텍스처를 생성합니다.

```

unsigned int brdfLUTTexture;
glGenTextures(1, &brdfLUTTexture);

// pre-allocate enough memory for the LUT texture.
glBindTexture(GL_TEXTURE_2D, brdfLUTTexture);
glTexImage2D(GL_TEXTURE_2D, 0, GL_RG16F, 512, 512, 0, GL_RG, GL_FLOAT, 0);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR); 

```


에픽 게임즈에서 권장하는 16비트 정밀도의 부동 소수점 형식을 사용합니다. 에지 샘플링으로 인한 아티팩트를 방지하려면 래핑 모드를 GL_CLAMP_TO_EDGE로 설정하십시오.

그런 다음, 동일한 프레임버퍼 객체를 재사용하고 NDC 화면 공간 쿼드에 대해 이 셰이더를 실행합니다.

```

glBindFramebuffer(GL_FRAMEBUFFER, captureFBO);
glBindRenderbuffer(GL_RENDERBUFFER, captureRBO);
glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 512, 512);
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, brdfLUTTexture, 0);

glViewport(0, 0, 512, 512);
brdfShader.use();
glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
RenderQuad();

glBindFramebuffer(GL_FRAMEBUFFER, 0);  

```


분할합 적분의 복잡한 BRDF 부분은 다음과 같은 결과를 제공해야 합니다.

![BRDF LUT](https://learnopengl.com/img/pbr/ibl_brdf_lut.png)

사전 필터링된 환경 맵과 BRDF 2D LUT를 모두 사용하여 분할 합 근사법에 따라 간접 반사광 적분을 재구성할 수 있습니다. 이렇게 결합된 결과는 간접 또는 주변 반사광으로 작용합니다.

IBL 반사율 계산 완료
------------------------------

간접 반사율 방정식을 제대로 작동시키려면 분할 합 근사치의 두 부분을 결합해야 합니다. 먼저 미리 계산된 조명 데이터를 PBR 셰이더 상단에 추가해 보겠습니다.

```

uniform samplerCube prefilterMap;
uniform sampler2D   brdfLUT;  

```


먼저, 반사 벡터를 사용하여 사전 필터링된 환경 맵을 샘플링함으로써 표면의 간접적인 반사광을 얻습니다. 표면 거칠기에 따라 적절한 밉 레벨을 샘플링하므로 표면이 거칠수록 반사광이 더 흐릿해집니다.

```

void main()
{
    [...]
    vec3 R = reflect(-V, N);   

    const float MAX_REFLECTION_LOD = 4.0;
    vec3 prefilteredColor = textureLod(prefilterMap, R,  roughness * MAX_REFLECTION_LOD).rgb;    
    [...]
}

```


사전 필터링 단계에서는 환경 맵을 최대 5개의 밉 레벨(0~4)까지만 컨볼루션했습니다. 이를 MAX_REFLECTION_LOD로 표기하여 (관련) 데이터가 없는 밉 레벨에서 샘플링하지 않도록 했습니다.

그런 다음 재질의 거칠기와 법선 벡터와 시점 벡터 사이의 각도를 고려하여 BRDF 조회 텍스처에서 샘플링합니다.

```

vec3 F        = FresnelSchlickRoughness(max(dot(N, V), 0.0), F0, roughness);
vec2 envBRDF  = texture(brdfLUT, vec2(max(dot(N, V), 0.0), roughness)).rg;
vec3 specular = prefilteredColor * (F * envBRDF.x + envBRDF.y);

```


BRDF 조회 텍스처에서 얻은 \\(F\_0\\)의 스케일과 편향(여기서는 간접 프레넬 결과 F를 직접 사용함)을 고려하여 이를 IBL 반사율 방정식의 왼쪽 사전 필터 부분과 결합하고 근사화된 적분 결과를 반사광으로 재구성합니다.

이를 통해 반사율 방정식의 간접 정반사 부분을 얻습니다. 이제, 이를 앞서 구한 확산 IBL 반사율 방정식 부분과 결합합니다. [마지막](https://learnopengl.com/PBR/IBL/Diffuse-irradiance) 이 장을 읽고 나면 PBR IBL의 전체 결과를 얻을 수 있습니다.

```

vec3 F = FresnelSchlickRoughness(max(dot(N, V), 0.0), F0, roughness);

vec3 kS = F;
vec3 kD = 1.0 - kS;
kD *= 1.0 - metallic;	  
  
vec3 irradiance = texture(irradianceMap, N).rgb;
vec3 diffuse    = irradiance * albedo;
  
const float MAX_REFLECTION_LOD = 4.0;
vec3 prefilteredColor = textureLod(prefilterMap, R,  roughness * MAX_REFLECTION_LOD).rgb;   
vec2 envBRDF  = texture(brdfLUT, vec2(max(dot(N, V), 0.0), roughness)).rg;
vec3 specular = prefilteredColor * (F * envBRDF.x + envBRDF.y);
  
vec3 ambient = (kD * diffuse + specular) * ao; 

```


프레넬 곱셈이 이미 포함되어 있으므로 반사광에 kS를 곱하지 않는다는 점에 유의하십시오.

이제 표면 거칠기와 금속성 특성이 서로 다른 구체들에 이 코드를 정확히 실행하면, 최종 PBR 렌더러에서 구체들의 실제 색상을 확인할 수 있습니다.

![표면 거칠기와 금속성 속성이 다양한 구체에 IBL(이미지 기반 조명)을 적용한 완전한 PBR(물리 기반 렌더링)을 OpenGL로 렌더링합니다.](https://learnopengl.com/img/pbr/ibl_specular_result.png)

우리는 과감하게 멋진 질감을 활용해 볼 수도 있을 거예요. [PBR 재료](http://freepbr.com/):

![텍스처가 적용된 구체에 IBL(이미지 기반 조명)을 사용한 완전한 PBR(물리 기반 렌더링)을 OpenGL로 렌더링합니다.](https://learnopengl.com/img/pbr/ibl_specular_result_textured.png)

또는 로드 [이 멋진 무료 3D PBR 모델](http://artisaverb.info/PBT.html) 앤드류 막시모프 지음

![3D PBR 모델에 IBL(이미지 기반 조명)을 적용한 완전한 PBR을 OpenGL로 렌더링합니다.](https://learnopengl.com/img/pbr/ibl_specular_result_model.png)

이제 조명이 훨씬 더 자연스러워 보인다는 데 모두 동의하실 거라고 생각합니다. 더 좋은 점은 어떤 환경 맵을 사용하든 조명이 물리적으로 정확해 보인다는 것입니다. 아래에서 여러 가지 미리 계산된 HDR 맵을 보실 수 있는데, 이 맵들은 조명 역학을 완전히 바꾸지만 조명 변수는 하나도 변경하지 않고도 여전히 물리적으로 정확해 보입니다!

![다양한 환경(변화하는 조명 조건 포함)에서 3D PBR 모델에 IBL(이미지 기반 조명)을 적용한 완전한 PBR을 OpenGL로 렌더링합니다.](https://learnopengl.com/img/pbr/ibl_specular_result_different_environments.png)

음, 이번 PBR 모험은 꽤 긴 여정이 되었네요. 단계가 많고 그만큼 잘못될 가능성도 많으니, 차근차근 단계를 진행해 나가세요. [구형 장면](https://learnopengl.com/code_viewer_gh.php?code=src/6.pbr/2.2.1.ibl_specular/ibl_specular.cpp) 또는 [질감이 있는 장면](https://learnopengl.com/code_viewer_gh.php?code=src/6.pbr/2.2.2.ibl_specular_textured/ibl_specular_textured.cpp) 막히는 부분이 있으면 코드 샘플(모든 셰이더 포함)을 참조하거나 댓글에서 질문해 보세요.

### 다음은 무엇인가요?

이 튜토리얼을 마치면 PBR이 무엇인지 명확하게 이해하고, 실제로 PBR 렌더러를 실행할 수 있게 되기를 바랍니다. 이 튜토리얼에서는 렌더링 루프 전에 애플리케이션 시작 부분에서 필요한 모든 PBR 이미지 기반 조명 데이터를 미리 계산했습니다. 이는 교육적인 목적에는 적합했지만, PBR을 실제로 사용하는 데에는 그다지 좋지 않았습니다. 첫째, 사전 계산은 매번 시작할 때마다 하는 것이 아니라 한 번만 하면 됩니다. 둘째, 여러 환경 맵을 사용하는 순간부터 매번 시작할 때마다 각 맵을 모두 사전 계산해야 하므로 계산량이 누적되기 쉽습니다.

이러한 이유로 일반적으로 환경 맵을 조도 및 사전 필터 맵으로 한 번만 미리 계산한 다음 디스크에 저장합니다(BRDF 통합 맵은 환경 맵에 의존하지 않으므로 한 번만 계산하거나 불러오면 됩니다). 즉, HDR 큐브맵과 밉 레벨을 저장하기 위한 사용자 지정 이미지 형식을 만들어야 합니다. 또는 밉 레벨 저장을 지원하는 .dds와 같은 기존 형식 중 하나로 저장(및 불러오기)할 수 있습니다.

또한, 이 튜토리얼에서는 PBR 파이프라인에 대한 이해를 돕기 위해 사전 계산된 IBL 이미지를 생성하는 과정을 포함하여 **전체** 프로세스를 설명했습니다. 하지만, 다음과 같은 훌륭한 도구들을 사용해도 충분히 잘 해낼 수 있을 것입니다. [cmftStudio](https://github.com/dariomanesku/cmftStudio) 또는 [IBL 베이커](https://github.com/derkreature/IBLBaker) 이러한 사전 계산된 지도를 생성해 드립니다.

지금까지 간과했던 부분 중 하나는 반사 프로브로 사용되는 사전 계산된 큐브맵, 즉 큐브맵 보간 및 시차 보정입니다. 이는 장면의 특정 위치에 여러 개의 반사 프로브를 배치하여 해당 위치의 큐브맵 스냅샷을 찍는 과정입니다. 이렇게 얻은 스냅샷을 해당 장면 부분의 IBL(이미지 기반 조명) 데이터로 컨볼루션할 수 있습니다. 카메라 주변을 기반으로 여러 프로브의 데이터를 보간함으로써, 배치할 반사 프로브의 개수에 따라 제한되는 고해상도 이미지 기반 조명을 구현할 수 있습니다. 예를 들어 밝은 야외 장면에서 어두운 실내 장면으로 이동할 때 이미지 기반 조명이 정확하게 업데이트될 수 있습니다. 향후 반사 프로브에 대한 튜토리얼을 작성할 예정이지만, 지금은 아래 Chetan Jags의 글을 참고하시면 도움이 될 것입니다.

추가 자료
---------------

*   [언리얼 엔진 4의 리얼 셰이딩](http://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf)이 글은 에픽 게임즈의 분할합 근사치를 설명합니다. IBL PBR 코드는 이 글을 기반으로 만들어졌습니다.
*   [물리 기반 셰이딩 및 이미지 기반 조명](http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/)트렌트 리드가 실시간으로 반사형 IBL을 PBR 파이프라인에 통합하는 방법에 대한 훌륭한 블로그 게시물을 작성했습니다.
*   [이미지 기반 조명](https://chetanjags.wordpress.com/2015/08/26/image-based-lighting/)체탄 재그스가 반사광 기반 이미지 기반 조명과 그 주의 사항들(광선 프로브 보간 포함)에 대해 매우 자세하게 설명한 글입니다.
*   [프로스트바이트를 PBR로 이전합니다](https://seblagarde.files.wordpress.com/2015/07/course_notes_moving_frostbite_to_pbr_v32.pdf)세바스티앙 라가르드와 샤를 드 루시에가 AAA 게임 엔진에 PBR을 통합하는 방법에 대해 잘 쓰여진 심층적인 개요입니다.
*   [물리 기반 렌더링 – 3부](https://jmonkeyengine.github.io/wiki/jme3/advanced/pbr_part3.html)JMonkeyEngine 팀에서 제공하는 IBL 조명 및 PBR에 대한 개괄적인 설명입니다.
*   [구현 참고 사항: 이미지 기반 조명을 위한 런타임 환경 맵 필터링](https://placeholderart.wordpress.com/2015/07/28/implementation-notes-runtime-environment-map-filtering-for-image-based-lighting/)패드릭 헤네시가 HDR 환경 맵 사전 필터링 및 샘플링 프로세스 최적화에 대해 자세히 설명한 글입니다.