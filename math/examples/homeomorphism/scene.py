from manim import *
import numpy as np

# Silent Cairo preview; no external assets or runtime I/O in this source.
config.renderer = "cairo"
config.pixel_width = 854
config.pixel_height = 480
config.frame_rate = 15
config.frame_height = 8
config.frame_width = 8 * 854 / 480
config.background_color = "#09131F"


class AstraFilm(ThreeDScene):
    """108 seconds, 1620 frames: 8 + 15 + 18 + 18 + 31 + 6 + 12.

    MATHEMATICAL MODEL -- unchanged from the approved geometry.
    X is the complete boundary of a rounded, thick ideal cup with one ordinary
    handle, no cracks, extra cavities, extra tunnels, or degenerate contacts.
    Y is the boundary of an ideal solid torus. Both have the subspace topology
    from R^3. The air opening is a depression in X, not a boundary component.
    Exterior, lip, interior, inner floor and underside belong to ONE surface.

    The common material domain is Q=(R/2pi Z)^2. _map implements exactly
    F_t = W_a(t) o P_t from the approved mathematics dossier. P_t has radial
    ellipse sections about (c_t,0,0). W_a(x,y,z)=(x,y,-1.7+q_a(x,y)(z+1.7)).
    H is clamped cubic smoothstep, a=.68*(1-H(t/.4)),
    lambda=H((t-.4)/.6). During film seconds 63--86, t=(seconds-63)/23.
    The first 9.2 s lift the depression; the next 13.8 s reshape the ring.

    PROOF / ILLUSTRATION BOUNDARY
    Inner-ellipse containment follows from
    1.65^2/4 + .85^2/2.56 = .9628515625 < 1.
    Thus ro>ri>0 and b>0, also during the prescribed coefficient interpolation.
    The xz polar angle uniquely recovers u; section ellipse coordinates
    uniquely recover v. q>=.32, and W_a has the continuous inverse
    z=(z_new+1.7)/q-1.7. Hence each exact F_t is an embedding of compact Q.
    F_1 o inverse(F_0) is the explicit homeomorphism for this exact model.
    This is NOT straight interpolation of endpoint vertex positions.

    Independently, a thick cup body is a ball with one ordinary 1-handle.
    Its boundary is compact, connected, orientable and genus one. Surface
    classification gives X homeomorphic to S^1 x S^1. On this class only,
    chi=2-2g; S^2 has chi=2 and the torus has chi=0, ruling out homeomorphism.
    Equal hole counts do not classify arbitrary spaces; homotopy equivalence
    is not homeomorphism. Abstract homeomorphism does not, by definition,
    assert ambient isotopy of specified embeddings.

    DISPLAY REVISION
    A fixed 96x64 base parameter grid is refined near the cup depression and
    at neighborhood boundaries. The resulting grid has 117x82 cells.
    Every cell uses the SAME fixed diagonal and two outward-wound triangles.
    There are no nonplanar quadrilateral faces, added caps, removed faces,
    camera-facing overlays over the cup, or endpoint crossfades.
    Cairo sorts the individual shaded triangles by its native depth rule.
    Small matching strokes address antialias seams, not missing geometry.
    Native painter sorting remains approximate and requires rendered review.

    All vertices retain their parameter coordinates for the entire film.
    Periodic seam copies denote the same material points. The coral open
    rectangle remains centered at (pi,3pi/2), with half-widths (.12,.16).
    The violet open rectangle is fixed at (.72,5.05), with half-widths
    (.27,.52), to occupy a broader front-facing portion of the handle.
    Its center is selected once, never selected again during the motion.
    Visible color edges identify neighborhoods; the mathematical rectangles
    are open and do not include their boundaries.

    Finite triangle-area, seam and connectivity checks are not a global
    collision test or a continuous-time rendered-motion proof. This source
    is not a new MP4, visual approval, independent audit or Jev verdict.
    """

    BG = "#09131F"
    CYAN = "#38B8CB"
    DEEP = "#14798F"
    GOLD = "#FFC857"
    CORAL = "#FA8879"
    VIOLET = "#B59BFF"
    WHITE_INK = "#F1F5FA"
    MUTED = "#A6B8CA"

    @staticmethod
    def _H(x):
        x = np.clip(x, 0.0, 1.0)
        return x * x * (3.0 - 2.0 * x)

    @classmethod
    def _map(cls, uv, t):
        uv = np.asarray(uv, dtype=float)
        u, v = uv[..., 0], uv[..., 1]
        cu, su = np.cos(u), np.sin(u)
        A = cu * cu / 4.0 + su * su / 2.56
        B = 0.6 * cu
        ro = (-B + np.sqrt(B * B + 2.56 * A)) / (2.0 * A)
        ri = 1.0 / np.sqrt(cu * cu / 0.45**2 + su * su / 0.85**2)
        lam = cls._H((t - 0.4) / 0.6)
        a = 0.68 * (1.0 - cls._H(t / 0.4))
        ro = (1.0 - lam) * ro + 1.95 * lam
        ri = (1.0 - lam) * ri + 1.05 * lam
        b = (1.0 - lam) * (0.18 + 0.46 * (1.0 - cu)) + 0.45 * lam
        c = 0.9 * (1.0 - lam)
        rho = (ro + ri) / 2.0 + (ro - ri) / 2.0 * np.cos(v)
        x = c + rho * cu
        y = b * np.sin(v)
        z = rho * su
        q = 1.0 - a * np.exp(-((x + 1.0)**2 + y * y) / 0.36)
        z = -1.7 + q * (z + 1.7)
        return np.stack((x, y, z), axis=-1)

    @staticmethod
    def _angle_distance(a, b):
        return np.abs((a - b + PI) % TAU - PI)

    @staticmethod
    def _screen_center(x, y=0):
        theta, phi = -75 * DEGREES, 55 * DEGREES
        right = np.array([-np.sin(theta), np.cos(theta), 0.0])
        up = np.array([-np.cos(phi) * np.cos(theta),
                       -np.cos(phi) * np.sin(theta), np.sin(phi)])
        return x * right + y * up

    def _rig(self, t=0.0, scale=1.0, center=None, marked=False):
        marker_uv = np.array([[PI, 1.5 * PI], [0.72, 5.05]])
        patch_half = np.array([[0.12, 0.16], [0.27, 0.52]])
        bu = np.linspace(0, TAU, 97)
        bv = np.linspace(0, TAU, 65)
        um = (bu[:-1] + bu[1:]) / 2
        vm = (bv[:-1] + bv[1:]) / 2

        def knots(base, extra):
            values = np.sort(np.concatenate((base, extra)))
            return values[np.r_[True, np.diff(values) > 1e-10]]

        # This refinement is computed ONCE in the material parameter domain.
        # No knots or connectivity change when the cup becomes a torus.
        us = knots(bu, np.concatenate((
            um[(um > 1.8) & (um < 2.95)],
            (marker_uv[:, 0, None]
             + np.array([-1, 1]) * patch_half[:, 0, None]).ravel(),
        )))
        vs = knots(bv, np.concatenate((
            vm[(vm < 0.65) | (vm > TAU - 0.65)],
            (marker_uv[:, 1, None]
             + np.array([-1, 1]) * patch_half[:, 1, None]).ravel(),
        )))
        uv = []
        faces = []
        for i in range(len(us) - 1):
            for j in range(len(vs) - 1):
                q00 = [us[i], vs[j]]
                q01 = [us[i], vs[j + 1]]
                q11 = [us[i + 1], vs[j + 1]]
                q10 = [us[i + 1], vs[j]]
                # The common diagonal is q00--q11, at every time t.
                for side, corners in enumerate((
                    [q00, q01, q11, q00],
                    [q00, q11, q10, q00],
                )):
                    face = ThreeDVMobject(
                        fill_color=self.CYAN, fill_opacity=1,
                        stroke_color=self.CYAN, stroke_width=0.10,
                    )
                    face.material_id = (i, j, side)
                    faces.append(face)
                    uv.append(corners)
        uv = np.asarray(uv, dtype=float)
        surf = VGroup(*faces)
        tunnel_uv = np.column_stack((
            np.linspace(0, TAU, 97), np.full(97, PI)
        ))
        # Short segments use ordinary Cairo depth occlusion.
        tunnel = VGroup(*[
            Line(ORIGIN, RIGHT, color=self.GOLD, stroke_width=2.8)
            .set_shade_in_3d(True)
            for _ in range(96)
        ])
        dots = VGroup(*[
            Sphere(radius=0.064, resolution=(8, 6),
                   fill_color=self.GOLD, checkerboard_colors=False,
                   stroke_width=0)
            for _ in range(2)
        ])
        dots.set_opacity(1 if marked else 0)
        rig = dict(
            surface=surf, tunnel=tunnel, dots=dots,
            group=VGroup(surf, tunnel, dots),
            uv=uv, mid=uv[:, :3].mean(axis=1),
            tunnel_uv=tunnel_uv, marker_uv=marker_uv,
            patch_half=patch_half, us=us, vs=vs,
            t=t, scale=scale,
            center=np.zeros(3) if center is None else np.asarray(center),
            marked=marked,
        )
        self._paint(rig)
        self._pose(rig)
        return rig

    def _paint(self, rig, region=None):
        mid = rig["mid"]
        unwarped = self._map(mid, 0.4)
        rr = np.sqrt((unwarped[:, 0] + 1.0)**2 + unwarped[:, 1]**2)
        zz = unwarped[:, 2]
        masks = {
            "outer": (np.abs(unwarped[:, 1]) > 0.72) & (zz < 0.9),
            "lip": (zz > 0.15) & (rr > 0.52) & (rr < 0.82),
            "inner": (zz > 0.15) & (rr > 0.25) & (rr < 0.52),
            "floor": (zz > 0.15) & (rr < 0.25),
            "underside": zz < -1.1,
        }
        highlight = masks.get(region, np.zeros(len(mid), dtype=bool))
        patches = []
        for center, half in zip(rig["marker_uv"], rig["patch_half"]):
            patches.append(
                (self._angle_distance(mid[:, 0], center[0]) < half[0])
                & (self._angle_distance(mid[:, 1], center[1]) < half[1])
            )
        for k, face in enumerate(rig["surface"]):
            u, v = mid[k]
            color = interpolate_color(
                ManimColor(self.DEEP), ManimColor(self.CYAN),
                0.70 + 0.18 * np.cos(u - 0.45)
            )
            if abs(v - PI) < 0.15:
                color = ManimColor("#B99443")
            if highlight[k]:
                color = ManimColor(self.GOLD)
            if rig["marked"]:
                if patches[0][k]:
                    color = ManimColor(self.CORAL)
                elif patches[1][k]:
                    color = ManimColor(self.VIOLET)
            face.set_fill(color, opacity=1)
            face.set_stroke(color, width=0.10, opacity=1)

    def _pose(self, rig, t=None, scale=None, center=None):
        if t is not None:
            rig["t"] = float(t)
        if scale is not None:
            rig["scale"] = float(scale)
        if center is not None:
            rig["center"] = np.asarray(center)
        t, scale, center = rig["t"], rig["scale"], rig["center"]
        p = scale * self._map(rig["uv"], t) + center
        a, b = p[:, :-1, :], p[:, 1:, :]
        # Three straight cubic edges per planar triangle. Existing objects
        # and fixed material vertices are updated; surfaces are not rebuilt.
        controls = np.stack((a, (2*a+b)/3, (a+2*b)/3, b), axis=2)
        controls = controls.reshape(len(p), 12, 3)
        for face, points in zip(rig["surface"], controls):
            face.set_points(points)
        tp = scale * self._map(rig["tunnel_uv"], t) + center
        for segment, start, end in zip(rig["tunnel"], tp[:-1], tp[1:]):
            segment.set_points_as_corners([start, end])
        dp = scale * self._map(rig["marker_uv"], t) + center
        for dot, point in zip(rig["dots"], dp):
            dot.move_to(point)

    def _txt(self, words, size=32, color=None, max_width=12.8):
        mob = Text(words, font="Microsoft YaHei", font_size=size,
                   color=color or self.WHITE_INK)
        if mob.width > max_width:
            mob.scale(max_width / mob.width)
        return mob

    def _pin(self, *mobs):
        for mob in mobs:
            mob.set_z_index(100)
        self.add_fixed_in_frame_mobjects(*mobs)

    def _unpin(self, *mobs):
        self.remove_fixed_in_frame_mobjects(*mobs)
        self.remove(*mobs)

    def _hud(self, title, line1="", line2="", formula=None,
             formula_at=(0, 2.35), formula_size=40):
        if hasattr(self, "_hud_group"):
            self._unpin(self._hud_group)
        title_mob = self._txt(title, 38, max_width=12.6).move_to([0, 3.52, 0])
        items = [title_mob]
        if line1:
            yy = -3.13 if line2 else -3.37
            items.append(self._txt(line1, 32).move_to([0, yy, 0]))
        if line2:
            items.append(self._txt(line2, 30, self.MUTED).move_to([0, -3.68, 0]))
        if formula:
            f = MathTex(formula, font_size=formula_size, color=self.WHITE_INK)
            if f.width > 12.5:
                f.scale(12.5 / f.width)
            f.move_to([formula_at[0], formula_at[1], 0])
            items.append(f)
        self._hud_group = VGroup(*items)
        self._pin(self._hud_group)

    def _blob(self, x):
        pts = np.array([
            [-1.45, 0.0, 0], [-1.0, 0.92, 0], [0.3, 1.08, 0],
            [1.3, 0.58, 0], [1.5, -0.55, 0], [0.3, -1.02, 0],
            [-1.1, -0.85, 0], [-1.45, 0.0, 0],
        ])
        return VMobject().set_points_smoothly(pts).set_fill(
            self.CYAN, 0.13
        ).set_stroke(self.CYAN, 2).shift(x * RIGHT - 0.15 * UP)

    def _correspondence(self):
        left, right = self._blob(-3.2), self._blob(3.2)
        lx = MathTex("X", font_size=36).move_to([-3.2, 1.52, 0])
        ly = MathTex("Y", font_size=36).move_to([3.2, 1.52, 0])
        base = VGroup(left, right, lx, ly)
        pairs = VGroup()
        positions = [(-0.55, 0.5), (0.28, -0.08), (-0.18, -0.65)]
        for (dx, dy), color in zip(
            positions, [self.GOLD, self.CORAL, self.VIOLET]
        ):
            p = np.array([-3.2 + dx, dy, 0])
            q = np.array([3.2 + dx, dy, 0])
            pairs.add(Dot(p, radius=0.075, color=color),
                      Dot(q, radius=0.075, color=color),
                      Arrow(p + 0.18*RIGHT, q - 0.18*RIGHT,
                            buff=0.04, stroke_width=1.5,
                            color=color, max_tip_length_to_length_ratio=0.035))
        return base, pairs

    def _attachment_marks(self, rig):
        # Analytical decomposition marks; no cuts or new surface components.
        seams = VGroup()
        for u in [1.1, TAU - 1.1]:
            vv = np.linspace(PI + 0.35, TAU - 0.35, 19)
            uv = np.column_stack((np.full(len(vv), u), vv))
            points = rig["scale"] * self._map(uv, rig["t"]) + rig["center"]
            for k in range(0, len(points)-1, 2):
                seams.add(Line(points[k], points[k+1],
                               stroke_width=3, color=self.GOLD)
                          .set_shade_in_3d(True))
        return seams

    def construct(self):
        self.set_camera_orientation(phi=55*DEGREES, theta=-85*DEGREES,
                                    zoom=1, focal_distance=30)
        self.camera.light_source.move_to([-4, -6, 8])
        top_rule = Line([-6.7, 3.08, 0], [6.7, 3.08, 0],
                        color="#244154", stroke_width=1)
        bottom_rule = Line([-6.7, -2.78, 0], [6.7, -2.78, 0],
                           color="#244154", stroke_width=1)
        tag = self._txt("几何示意", 21, self.MUTED).move_to([6.0, 2.80, 0])
        self._pin(top_rule, bottom_rule, tag)

        # 1. 00--08 s | frames 0--119 | 120 frames.
        cup = self._rig(0, 1.05, self._screen_center(-3.1, -0.1))
        tire = self._rig(1, 1.05, self._screen_center(3.1, -0.1))
        self.add(cup["group"], tire["group"])
        self._hud("水杯与轮胎，为什么同胚？", "比较完整边界曲面")
        self.wait(3)
        self.move_camera(theta=-75*DEGREES, run_time=3, rate_func=smooth)
        self._hud("水杯与轮胎，为什么同胚？",
                  "杯口的凹陷，与把手的隧道一样吗？")
        self.wait(2)

        # 2. 08--23 s | frames 120--344 | 225 frames.
        # Intro, three axioms, and scope: five stable 45-frame readings.
        self.remove(cup["group"])
        self._pose(tire, scale=0.98, center=self._screen_center(3.3, -0.15))
        tire["marked"] = True
        tire["dots"].set_opacity(1)
        self._paint(tire)
        self._hud("什么是拓扑？", "τ 中的集合叫开集",
                  formula=r"(X,\tau)", formula_at=(-2.8, 0.65),
                  formula_size=58)
        self.wait(3)
        self._hud("开集族满足三个条件", "空集与整个空间都在其中",
                  formula=r"\varnothing,\ X\in\tau", formula_at=(-2.8, 0.65))
        self.wait(3)
        disks = VGroup(
            Circle(radius=0.56, color=self.CORAL, stroke_width=1.2)
            .set_fill(self.CORAL, 0.28).move_to([-3.12, -0.85, 0]),
            Circle(radius=0.56, color=self.VIOLET, stroke_width=1.2)
            .set_fill(self.VIOLET, 0.28).move_to([-2.48, -0.85, 0]),
        )
        self._pin(disks)
        self._hud("开集族满足三个条件", "任意并仍是开集", "各个 U 都是开集",
                  formula=r"\bigcup_{\alpha\in I}U_\alpha\in\tau",
                  formula_at=(-2.8, 0.65))
        self.wait(3)
        self._hud("开集族满足三个条件", "有限交仍是开集", "各个 U 都是开集",
                  formula=r"\bigcap_{k=1}^{n}U_k\in\tau",
                  formula_at=(-2.8, 0.65))
        self.wait(3)
        self._unpin(disks)
        self._hud("拓扑描述邻近与连续", "不指定长度、角度或体积",
                  "一般拓扑空间不必嵌入三维")
        self.wait(3)

        # 3. 23--41 s | frames 345--614 | 270 frames.
        # Each homeomorphism condition: 45 frames. Preimages: 75 + 60.
        self.remove(tire["group"])
        base, pairs = self._correspondence()
        self._pin(base, pairs)
        self._hud("同胚：双向连续的一一对应", "① 双射",
                  "每个点恰有一个对应",
                  formula=r"f:X\longrightarrow Y")
        self.wait(3)
        self._hud("同胚：双向连续的一一对应", "② 映射连续",
                  "邻近关系由映射保持",
                  formula=r"f:X\longrightarrow Y")
        self.wait(3)
        self._hud("同胚：双向连续的一一对应", "③ 逆函数也连续",
                  "此处的逆函数以双射为前提",
                  formula=r"f^{-1}:Y\longrightarrow X")
        self.wait(3)
        self._unpin(pairs)
        target = Circle(radius=0.67, color=self.VIOLET, stroke_width=1.5)
        target.set_fill(self.VIOLET, 0.4).move_to([3.2, -0.1, 0])
        source = Ellipse(width=1.75, height=1.12, color=self.VIOLET,
                         stroke_width=1.5, fill_opacity=0.4)
        source.move_to([-3.2, -0.1, 0])
        set_labels = VGroup(
            MathTex("V", font_size=34).move_to([3.2, -0.1, 0]),
            MathTex(r"f^{-1}(V)", font_size=32).move_to([-3.2, -0.1, 0])
        )
        reverse = Arrow([1.25, -0.1, 0], [-1.25, -0.1, 0],
                        buff=0.06, color=self.VIOLET, stroke_width=2)
        self._pin(target, source, set_labels, reverse)
        self._hud("连续：开集的原像仍开", "每个目标开集的原像，在源空间中开",
                  formula=r"\forall V\in\tau_Y,\quad f^{-1}(V)\in\tau_X")
        self.wait(5)
        self._unpin(reverse)
        self._hud("原像，不等于逆函数", "这里是集合原像", "任何函数都可取原像",
                  formula=r"f^{-1}(V)=\{x\in X\mid f(x)\in V\}",
                  formula_size=38)
        self.wait(4)
        self._unpin(base, target, source, set_labels)

        # 4. 41--59 s | frames 615--884 | 270 frames.
        # Stable regions: outer 2 s, lip 2 s, inner 2 s, floor 2 s.
        # Camera travel does not count toward these stable holds.
        main = self._rig(0, 1.34, self._screen_center(0, -0.1))
        self.add(main["group"])
        self._paint(main, "outer")
        self._hud("我们比较完整的杯面", "有厚度、无裂缝、一个完整普通把手",
                  "外壁")
        self.wait(2)                                      # 41--43
        self.move_camera(phi=35*DEGREES, zoom=1.04,
                         run_time=1, rate_func=smooth)     # 43--44
        self._paint(main, "lip")
        self._hud("我们比较完整的杯面", "杯口是凹陷；内外表面连成一张",
                  "杯沿")
        self.wait(2)                                      # 44--46
        self._paint(main, "inner")
        self._hud("我们比较完整的杯面", "杯口是凹陷；内外表面连成一张",
                  "内壁")
        self.wait(2)                                      # 46--48
        self._paint(main, "floor")
        self._hud("我们比较完整的杯面", "杯口是凹陷；内外表面连成一张",
                  "内底")
        self.wait(2)                                      # 48--50
        self._paint(main, "underside")
        self._hud("底部也属于完整表面", "外底与内底之间有材料厚度",
                  "外底")
        self.move_camera(phi=110*DEGREES, zoom=1,
                         run_time=1, rate_func=smooth)     # 50--51
        self.wait(2)                                      # 51--53
        self.move_camera(phi=55*DEGREES, theta=-75*DEGREES,
                         run_time=1, rate_func=smooth)     # 53--54
        self._paint(main)
        self._hud("完整杯面没有边界", "轮胎＝理想环形体的边界",
                  "两者均取三维空间的子空间拓扑")
        self.wait(3)                                      # 54--57
        self._hud("完整杯面没有边界", "无额外空腔、隧道或退化接触",
                  "金色曲线定位贯通把手的隧道")
        self.wait(2)                                      # 57--59

        # 5. 59--90 s | frames 885--1349 | 465 frames.
        # Cup hold: 60 frames. Continuous F_t: 138+105+102=345 frames.
        # Torus endpoint: 30-frame camera move, then 30-frame static hold.
        main["marked"] = True
        main["dots"].set_opacity(1)
        self._paint(main)
        self._hud("同一张曲面，连续改变形状", "形变帮助理解，不是同胚的定义",
                  "同胚不自动给出指定嵌入间的环境同痕")
        self.wait(4)                                      # 59--63
        progress = ValueTracker(0)
        main["group"].add_updater(
            lambda mob: self._pose(main, t=progress.get_value())
        )
        self._hud("凹陷可以逐渐变浅", "金点与彩色邻域，跟随同一材料",
                  "色块边线仅作识别")
        self.play(progress.animate.set_value(0.4),
                  run_time=138 / 15, rate_func=linear)     # 63--72.2
        self._hud("拉伸、弯曲、压扁", "材料点保持一一对应",
                  "把手隧道持续存在")
        self.play(progress.animate.set_value(0.4 + 0.6 * 105 / 207),
                  run_time=105 / 15, rate_func=linear)     # 72.2--79.2
        self._hud("连接关系保持不变", "不撕裂、不粘接",
                  "不合并不同材料点")
        self.play(progress.animate.set_value(1),
                  run_time=102 / 15, rate_func=linear)     # 79.2--86
        main["group"].clear_updaters()
        self._pose(main, t=1)
        self._hud("贯通隧道仍在", "现在是理想环面",
                  formula=r"S^1\times S^1", formula_at=(0, 2.67))
        self.move_camera(theta=-65*DEGREES, run_time=2, rate_func=smooth)
        self.wait(2)                                      # 86--90

        # 6. 90--96 s | frames 1350--1439 | 90 frames.
        # A structural explanation independent of the rendered deformation.
        self.remove(main["group"])
        self.set_camera_orientation(phi=55*DEGREES, theta=-75*DEGREES, zoom=1)
        structure = self._rig(0, 0.94, self._screen_center(-3.1, -0.2))
        self._pose(tire, t=1, scale=0.94,
                   center=self._screen_center(3.1, -0.2))
        tire["marked"] = False
        tire["dots"].set_opacity(0)
        self._paint(tire)
        seams = self._attachment_marks(structure)
        self.add(structure["group"], tire["group"], seams)
        self._hud("依据来自模型与定理", "厚壁杯体＋一个普通把手",
                  "完整边界：闭合、连通、可定向")
        self.wait(3)
        self._hud("曲面分类定理", "闭合＝紧致且无边界",
                  "动画是几何示意；数学论证独立给出",
                  formula=r"g=1,\qquad X\cong S^1\times S^1")
        self.wait(3)

        # 7. 96--108 s | frames 1440--1619 | 180 frames.
        # Four stable 45-frame readings; no epsilon-subtracted waits.
        self.remove(structure["group"], seams)
        sphere = Sphere(radius=1.55, resolution=(32, 16),
                        checkerboard_colors=False, fill_color="#8EBAD1",
                        stroke_color="#8EBAD1", stroke_width=0.2)
        sphere.move_to(self._screen_center(-3.1, -0.2))
        self.add(sphere)
        self._hud("为什么不能与球面同胚？", "比较闭合、连通、可定向曲面",
                  formula=r"S^2:\ g=0,\ \chi=2\qquad S^1\times S^1:\ g=1,\ \chi=0",
                  formula_size=34)
        self.wait(3)
        self._hud("欧拉示性数是同胚不变量", "适用范围：闭合连通可定向曲面",
                  formula=r"\chi=2-2g")
        self.wait(3)
        self._hud("欧拉示性数不同，所以不同胚", "球面没有把手；环面有一个把手",
                  formula=r"S^2\not\cong S^1\times S^1")
        self.wait(3)
        self._pose(structure, scale=0.72,
                   center=self._screen_center(-4.55, -0.25))
        self._pose(tire, scale=0.76, center=self._screen_center(0, -0.25))
        sphere.scale(0.80).move_to(self._screen_center(4.55, -0.25))
        self.add(structure["group"])
        relation = MathTex(r"\cong", r"\not\cong", font_size=58,
                           color=self.GOLD)
        relation[0].move_to([-2.25, -0.1, 0])
        relation[1].move_to([2.3, -0.1, 0])
        self._pin(relation)
        self._hud("同胚保留拓扑结构", "杯面与环面同胚；与球面不同胚",
                  "“洞数相同”不是一般空间的完整判据")
        self.wait(3)
