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
        # 1. მშობელი კლასის ინიციალიზაცია
        super().__post_init__()

        # --- რობოტის და სცენის კონფიგურაცია ---
        self.scene.robot = UNITREE_GO2_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
        self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base"
        
        # რელიეფის სკალირება მცირე რობოტისთვის
        self.scene.terrain.terrain_generator.sub_terrains["boxes"].grid_height_range = (0.025, 0.1)
        self.scene.terrain.terrain_generator.sub_terrains["random_rough"].noise_range = (0.01, 0.06)
        
        # მოქმედებების მასშტაბი (ნაკლები "ნერვული" მოძრაობისთვის)
        self.actions.joint_pos.scale = 0.25

        # --- 2. Domain Randomization (Sim-to-Real) ---
        # ვიყენებთ შემოწმებას, რადგან Isaac Lab-ის ვერსიებში ზოგი Dict-ია, ზოგი ConfigClass

        # მასის რანდომიზაცია
        if hasattr(self.events, "add_base_mass"):
            target = self.events.add_base_mass
            params = target["params"] if isinstance(target, dict) else target.params
            params["mass_distribution_params"] = (-1.0, 3.0)
            params["asset_cfg"].body_names = "base"

        # ხელის კვრა (Push Robot)
        if hasattr(self.events, "push_robot"):
            target = self.events.push_robot
            params = target["params"] if isinstance(target, dict) else target.params
            params["velocity_range"] = {"x": (-0.8, 0.8), "y": (-0.8, 0.8)}

        # ხახუნის რანდომიზაცია (Friction)
        if hasattr(self.events, "terrain_material_properties"):
            target = self.events.terrain_material_properties
            params = target["params"] if isinstance(target, dict) else target.params
            params["static_friction_range"] = (0.4, 1.25)
            params["dynamic_friction_range"] = (0.4, 1.25)

        # --- 3. Observation Noise ---
        # IMU და სიჩქარის ხმაური
        self.observations.policy.base_lin_vel.noise.n_min = -0.1
        self.observations.policy.base_lin_vel.noise.n_max = 0.1
        
        # ლიდარის (Height Scan) ხმაური
        if hasattr(self.observations.policy, "height_scan"):
            self.observations.policy.height_scan.noise.n_min = -0.05
            self.observations.policy.height_scan.noise.n_max = 0.05

        # ბრძანების დაყოვნება (Action Delay)
        self.actions.joint_pos.delay = (1, 2)

        # --- 4. Rewards & Terminations ---
        # ფეხების ჰაერში ყოფნის დრო
        self.rewards.feet_air_time.params["sensor_cfg"].body_names = ".*_foot"
        self.rewards.feet_air_time.weight = 0.02
        
        # არასასურველი კონტაქტები (მუხლები)
        if self.rewards.undesired_contacts is not None:
            self.rewards.undesired_contacts.weight = -1.0
            self.rewards.undesired_contacts.params["sensor_cfg"].body_names = ".*_thigh"

        # ტერმინაცია ბაზის კონტაქტისას
        self.terminations.base_contact.params["sensor_cfg"].body_names = "base"
        
        # სიჩქარის მიყოლის წონები
        self.rewards.track_lin_vel_xy_exp.weight = 1.5
        self.rewards.track_ang_vel_z_exp.weight = 0.75

        # RecordVideo: eye/lookat are world-axis offsets from viewer_origin (see ViewportCameraController).
        # With origin_type=asset_root the origin follows the robot but offsets do NOT yaw with the body,
        # so forward walking often looks "sideways" on screen. env + env_index fixes the camera to env_0
        # so the robot moves through the frame like a normal yard shot (wider = less zoom).
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
        # Smaller scene for play / video
        self.scene.num_envs = 32
        self.scene.env_spacing = 2.5
        # Match training cap (0); use None only if you want random terrain levels at play time.
        self.scene.terrain.max_init_terrain_level = 0
        # reduce the number of terrains to save memory
        if self.scene.terrain.terrain_generator is not None:
            self.scene.terrain.terrain_generator.num_rows = 5
            self.scene.terrain.terrain_generator.num_cols = 5
            self.scene.terrain.terrain_generator.curriculum = False

        # Wider shot for tiled play (optional): uncomment to pull camera farther from env_0.
        # self.viewer.eye = (12.0, 12.0, 7.0)

        self.observations.policy.enable_corruption = False
        
        # 2. ვთიშავთ რანდომიზებულ მოვლენებს (რომ ტესტისას რობოტს ხელი არ ჰკრან)
        if hasattr(self.events, "base_external_force_torque"):
            self.events.base_external_force_torque = None
            
        if hasattr(self.events, "push_robot"):
            self.events.push_robot = None
            
        # 3. ვთიშავთ მასის რანდომიზაციას ტესტირებისას
        if hasattr(self.events, "add_base_mass"):
            self.events.add_base_mass = None