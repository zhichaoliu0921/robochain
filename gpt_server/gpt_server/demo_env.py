import numpy as np
from robopal.envs.task_ik_ctrl_env import PosCtrlEnv
import robopal.commons.transform as T


def primitive(func, checker=None):
    """ primitive flag, no practical effect. """

    def primitive_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return primitive_wrapper


class GraspingEnv(PosCtrlEnv):
    def __init__(self,
                 robot=None,
                 is_render=True,
                 renderer="viewer",
                 control_freq=20,
                 is_interpolate=True,
                 is_pd=True,
                 ):
        super().__init__(
            robot=robot,
            is_render=is_render,
            renderer=renderer,
            control_freq=control_freq,
            is_interpolate=is_interpolate,
            is_pd=is_pd
        )
        self.p_cart = 0.8
        self.d_cart = 0.05
        self.p_quat = 0.8
        self.d_quat = 0.05

        
        
        self.init_pos, self.init_rot = self.kdl_solver.fk(self.robot.single_arm.arm_qpos, rot_format='quaternion')
        self.action = np.concatenate((self.init_pos, np.zeros(1)), axis=0)
        # can_list = ['red_block', 'blue_block', 'green_block']
        # self.can_pos, self.can_quat = self.get_obj_pose(can_list)

    def reset(self):
        super().reset()
        # init_pos, init_rot = self.kdl_solver.getEeCurrentPose(self.robot.single_arm.arm_qpos)
        self.move(self.init_pos, self.init_rot)
        # self.move(init_pos, self.can_quat['blue_block'])

    @primitive
    def get_obj_pose(self, obj_name):
        pos = self.mj_data.body(obj_name).xpos.copy()
        pos[2] -= 0.31
        quat = self.mj_data.body(obj_name).xquat.copy()
        return pos, quat

    @primitive
    def move(self, pos, quat):
        def checkArriveState(state):
            current_pos, current_quat = self.get_current_pose()
            error = np.sum(np.abs(state[:3] - current_pos)) + np.sum(np.abs(state[3:] - current_quat))
            if error <= 0.01:
                return True
            return False

        while True:
            self.action = np.concatenate((pos, quat), axis=0)
            self.step(self.action)
            if self.is_render:
                self.render()
            if checkArriveState(self.action):
                break

    @primitive
    #def grab(self, obj_name):
    #    self.gripper_ctrl("open")
    #    obj_pos, obj_quat = self.get_obj_pose(obj_name)
    #    self.move(np.add(obj_pos, np.array([0, 0, 0.1])), obj_quat)
    #    self.move(obj_pos, obj_quat)
    #    self.gripper_ctrl("close")
    #    end_pos, end_quat = self.get_current_pose()
    #    self.move(np.add(end_pos, np.array([0, 0, 0.1])), end_quat)

    @primitive
    def gripper_ctrl(self, cmd: str):
        if cmd == "open":
            self.mj_data.actuator("0_gripper_l_finger_joint").ctrl = 20
        elif cmd == "close":
            self.mj_data.actuator("0_gripper_l_finger_joint").ctrl = -20
        step = 0
        while True:
            step += 1
            self.step(self.action)
            if self.is_render:
                self.render()
            if step > 80:
                break

    @primitive
    def get_current_pose(self):
        return self.kdl_solver.fk(self.robot.single_arm.arm_qpos, rot_format='quaternion')

def make_env():
    from robopal.assets.robots.diana_med import DianaGraspMultiObjs
    env = GraspingEnv(
        robot=DianaGraspMultiObjs(),
        renderer="viewer",
        is_render=True,
        control_freq=200,
        is_interpolate=False,
        is_pd=True
    )
    return env
