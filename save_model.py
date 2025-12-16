from safetensors.torch import load_file
import torch

state_dict = load_file("robot_NLP_model/model.safetensors")
torch.save(state_dict, "robot_NLP_model/pytorch_model.bin")

print("Converted to pytorch_model.bin ✅")
