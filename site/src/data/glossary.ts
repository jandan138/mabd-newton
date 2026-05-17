export const glossary = {
  ABD: "Affine Body Dynamics：用仿射变换表示近刚体/可变形体的动力学方法。",
  "M-ABD": "Multi-Affine-Body Dynamics：把 ABD 扩展到多体、关节和拓扑求解的框架。",
  affine: "仿射变换：线性变换加平移，常写作 x = A xbar + t。",
  DOF: "Degree of Freedom，自由度；描述系统状态所需的独立数字数量。",
  SVD: "Singular Value Decomposition，奇异值分解；把矩阵拆成两个旋转/正交因子和一个缩放因子。",
  "polar decomposition": "极分解；把变形矩阵拆成旋转部分和对称拉伸部分。",
  KKT: "Karush-Kuhn-Tucker 条件；带约束优化和约束动力学中的块线性系统形式。",
  Jacobian: "Jacobian 矩阵；描述一个量对另一个量的一阶变化关系。",
  Hessian: "Hessian 矩阵；二阶导数矩阵，常表示局部曲率或刚度。",
  "implicit Euler": "隐式欧拉；用下一时刻状态计算力和速度的时间积分方法，通常需要解方程。",
  "co-rotational": "共旋转方法；先把整体旋转分离出去，再在线性化坐标中处理弹性变形。",
  provenance: "来源记录；说明数据、代码、论文材料或实验结果来自哪里以及如何验证。",
};

export type GlossaryTerm = keyof typeof glossary;
