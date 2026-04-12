# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from isaaclab.utils import configclass

from isaaclab_tasks.manager_based.locomotion.velocity.velocity_env_cfg import LocomotionVelocityRoughEnvCfg

##
# Pre-defined configs
##
from isaaclab_assets.robots.unitree import UNITREE_GO2_CFG  # isort: skip


@configclass
class UnitreeGo2RoughEnvCfg(LocomotionVelocityRoughEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()
        # 2. 🔥 აქ ვამცირებთ ხმაურს Observations-ისთვის 
        # Height Scan ხმაურის დაწევა 0.02-მდე (2 სმ)
        if hasattr(self.observations.policy, "height_scan"):
            self.observations.policy.height_scan.noise.n_min = -0.02
            self.observations.policy.height_scan.noise.n_max = 0.02

        # სხეულის სიჩქარეების ხმაურის შემცირება უფრო სტაბილური სწავლისთვის
        self.observations.policy.base_lin_vel.noise.n_min = -0.05
        self.observations.policy.base_lin_vel.noise.n_max = 0.05
        self.scene.robot = UNITREE_GO2_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base"
        # scale down the terrains because the robot is small
        self.scene.terrain.terrain_generator.sub_terrains["boxes"].grid_height_range = (0.025, 0.1)
        self.scene.terrain.terrain_generator.sub_terrains["random_rough"].noise_range = (0.01, 0.06)
        self.scene.terrain.terrain_generator.sub_terrains["random_rough"].noise_step = 0.01

        # reduce action scale
        self.actions.joint_pos.scale = 0.25

        # event
        self.events.push_robot = None
        self.events.add_base_mass.params["mass_distribution_params"] = (-1.0, 3.0)
        self.events.add_base_mass.params["asset_cfg"].body_names = "base"
        self.events.base_external_force_torque.params["asset_cfg"].body_names = "base"
        self.events.reset_robot_joints.params["position_range"] = (1.0, 1.0)
        self.events.reset_base.params = {
            "pose_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5), "yaw": (-3.14, 3.14)},
            "velocity_range": {
                "x": (0.0, 0.0),
                "y": (0.0, 0.0),
                "z": (0.0, 0.0),
                "roll": (0.0, 0.0),
                "pitch": (0.0, 0.0),
                "yaw": (0.0, 0.0),
            },
        }
        self.events.base_com = None

        # rewards
        self.rewards.feet_air_time.params["sensor_cfg"].body_names = ".*_foot"
        self.rewards.feet_air_time.weight = 0.02

        # აი აქ არის ცვლილება:
        if self.rewards.undesired_contacts is not None:
            self.rewards.undesired_contacts.weight = -1.0
            # ვამატებთ ამ ხაზს, რომ მშობელი კლასის ".*THIGH" გადაიწეროს სწორი სახელით
            self.rewards.undesired_contacts.params["sensor_cfg"].body_names = ".*_thigh"
            

        self.rewards.dof_torques_l2.weight = -0.0002
        self.rewards.track_lin_vel_xy_exp.weight = 1.5
        self.rewards.track_ang_vel_z_exp.weight = 0.75
        self.rewards.dof_acc_l2.weight = -2.5e-7

        # terminations
        self.terminations.base_contact.params["sensor_cfg"].body_names = "base"

        # RecordVideo: eye/lookat are offsets from viewer_origin in world axes (not robot body).
        # asset_root + big offsets → empty frame or “sideways” motion. Use env_0-fixed camera.
        self.viewer.origin_type = "env"
        self.viewer.env_index = 0
        self.viewer.asset_name = None
        self.viewer.eye = (8.0, 8.0, 5.5)
        self.viewer.lookat = (0.0, 0.0, 0.45)


@configclass
class UnitreeGo2RoughEnvCfg_PLAY(UnitreeGo2RoughEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()
        self.scene.num_envs = 32
        self.scene.env_spacing = 2.5
        self.scene.terrain.max_init_terrain_level = 0
        if self.scene.terrain.terrain_generator is not None:
            self.scene.terrain.terrain_generator.num_rows = 5
            self.scene.terrain.terrain_generator.num_cols = 5
            self.scene.terrain.terrain_generator.curriculum = False

        # Default: no obs corruption (Hydra can turn on for stress tests).
        self.observations.policy.enable_corruption = False
        self.events.base_external_force_torque = None
        # Keep push_robot, add_base_mass, physics_material so Hydra can stress them
        # (see isaac-lab-experiments docs/STRESS_TEST.md).

        # Wider shot: uncomment
        # self.viewer.eye = (12.0, 12.0, 7.0)
