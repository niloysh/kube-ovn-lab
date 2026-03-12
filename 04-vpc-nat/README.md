# VPC NAT

Need to cleanup Gateway IP after deletion.
```bash
kubectl rollout restart deployment kube-ovn-controller -n kube-system
```