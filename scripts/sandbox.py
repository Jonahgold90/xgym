from dataclasses import dataclass
import os
import os.path as osp
import time

import cv2
import draccus
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from xgym.controllers import (
    SpaceMouseController,
)
from xgym.gyms import Lift


@dataclass
class RunCFG:
    task: str = input("Task: ").lower()
    base_dir: str = osp.expanduser("~/data")
    time: str = time.strftime("%Y%m%d-%H%M%S")
    env_name: str = f"xgym-sandbox-{task}-v0-{time}"
    data_dir: str = osp.join(base_dir, env_name)

    nsteps: int = 30
    nepisodes: int = 100


plt.switch_backend("Agg")


def plot(actions):
    x, y, z, roll, pitch, yaw, gripper = actions.T
    time = np.arange(len(x))

    fig, ax = plt.subplots()
    ax.plot(time, x, label="x")
    ax.plot(time, y, label="y")
    ax.plot(time, z, label="z")
    ax.plot(time, roll, label="roll")
    ax.plot(time, pitch, label="pitch")
    ax.plot(time, yaw, label="yaw")
    ax.plot(time, gripper, label="gripper")
    ax.legend()

    canvas = FigureCanvas(fig)
    canvas.draw()
    img = np.frombuffer(canvas.tostring_rgb(), dtype="uint8")
    img = img.reshape(canvas.get_width_height()[::-1] + (3,))
    plt.close(fig)

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    return img


@draccus.wrap()
def main(cfg: RunCFG):
    os.makedirs(cfg.data_dir, exist_ok=True)

    agent = SpaceMouseController()

    # env = gym.make("xgym/stack-v0")
    env = Lift(out_dir=cfg.data_dir, random=True)

    freq = 10  # hz
    dt = 1 / freq

    hist = np.zeros(7)

    for ep in tqdm(range(cfg.nepisodes), desc="Episodes"):
        obs = env.reset()
        env.set_mode(7)
        time.sleep(0.4)
        env.start_record()

        # timestep = env.reset()
        # obs = timestep.observation
        for _ in tqdm(range(int(cfg.nsteps) * freq), desc=f"EP{ep}"):  # 3 episodes
            tic = time.time()
            print("\n" * 3)

            # obs["img"] = jax.tree_map(
            # lambda x: cv2.resize(np.array(x), (224, 224)), obs["img"]
            # )

            # print(obs["img"].keys())

            # myimg = obs["img"]["camera_10"]
            # primary = obs["img"]["camera_6"]

            np.set_printoptions(suppress=True)

            action = agent.read()
            action[-1] += env.gripper / env.GRIPPER_MAX
            print(f"action: {action.round(4)}")

            pose = env.position.to_vector()
            pose[:3] /= int(1e3)
            pose[-1] /= env.GRIPPER_MAX
            # hist = np.vstack([hist, pose])
            # img = plot(hist)

            # action[:3] *= int(1e2)
            # action[-1] =  0.2 if action[-1] < 0.8 else 1  # less gripper

            # cv2.imshow( "data Environment", img,)
            # cv2.cvtColor(cu.tile(cu.writekeys(obs["img"])), cv2.COLOR_RGB2BGR),
            # cv2.waitKey(1)  # 1 ms delay to allow for rendering

            env.send(action)

            # obs, done, info = env.observation(), False, {}
            done = env._done

            toc = time.time()
            elapsed = toc - tic
            time.sleep(max(0, dt - elapsed))  # 5hz

            print(f"done: {done}")
            if done:
                break

            # timestep = env.step(action)
            # obs = timestep.observation

        env.stop_record()
        env.flush()
        # env.auto_reset()

    env.reset()
    env.close()

    quit()


if __name__ == "__main__":
    main()
