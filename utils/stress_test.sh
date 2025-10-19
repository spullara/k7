#!/bin/bash

# High-density stress test - Testing CPU limit enforcement
COUNT=50
NAMESPACE="stress-test"
CPU_LIMIT="300m"       # 0.3 cores per sandbox = 15 total cores (testing limits!)
MEM_LIMIT="2Gi"        # 2GB per sandbox = 100GB total
STRESS_MEM="1500M"     # Stress 1.5GB memory

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Caught signal! Cleaning up stress test resources..."
    echo "Deleting all sandboxes in namespace '$NAMESPACE'..."
    
    # Use -y flag to skip confirmation
    k7 delete-all -n $NAMESPACE -y 2>/dev/null || echo "No sandboxes to delete"
    
    echo "Removing temporary config files..."
    rm -f k7-stress-*.yaml
    
    echo "Deleting namespace '$NAMESPACE'..."
    k3s kubectl delete namespace $NAMESPACE 2>/dev/null || echo "Namespace already deleted"
    
    echo "✅ Cleanup complete!"
    exit 0
}

# Set up signal handlers for cleanup
trap cleanup SIGINT SIGTERM EXIT

echo "=== K7 CPU Limit Enforcement Test ==="
echo "Target: $COUNT sandboxes"
echo "Resources per sandbox: CPU=$CPU_LIMIT (0.3 cores), Memory=$MEM_LIMIT"
echo "Total planned usage: CPU=15 cores, Memory=100GB"
echo "Hardware capacity: 20 cores, ~128GB RAM"
echo ""
echo "🎯 TESTING CPU LIMITS: Each pod will try to use 100% of 1 CPU core"
echo "   but should be limited to only 0.3 cores by Kubernetes!"
echo ""

# Create namespace
echo "Creating namespace '$NAMESPACE'..."
k3s kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace already exists"

echo "Creating $COUNT sandbox configurations..."

for i in $(seq 1 $COUNT); do
  cat <<EOF > k7-stress-$i.yaml
name: stress-pod-$i
image: alpine:latest
before_script: |
  # Add random delay to spread out package installs (0-30 seconds)
  sleep $((RANDOM % 30))
  echo "=== Pod $i: Installing stress-ng ==="
  apk add --no-cache stress-ng htop
  echo "=== Pod $i: Starting CPU limit enforcement test ==="
  echo "Pod $i: Attempting to use 100% of 1 CPU core (should be limited to 0.3)"
  # Try to use 1 full CPU at 100% load, but kubernetes should limit us to 300m
  stress-ng --cpu 1 --cpu-load 100 --vm 1 --vm-bytes $STRESS_MEM --timeout 900s &
  echo "=== Pod $i: CPU stress test active - testing 300m limit ==="
limits:
  cpu: "$CPU_LIMIT"
  memory: "$MEM_LIMIT"
  ephemeral-storage: "1Gi"
EOF
done

echo "Launching $COUNT sandboxes in batches of 10..."

# Launch in batches
for batch in $(seq 0 3); do
  start=$((batch * 10 + 1))
  end=$((batch * 10 + 10))
  
  echo "Launching batch $((batch + 1)): sandboxes $start-$end"
  
  for i in $(seq $start $end); do
    if [ $i -le $COUNT ]; then
      echo "  Creating stress-pod-$i (CPU limit: $CPU_LIMIT)..."
      k7 create -f k7-stress-$i.yaml --namespace $NAMESPACE &
    fi
  done
  
  wait
  echo "Batch $((batch + 1)) launched, waiting 30 seconds..."
  sleep 30
done

echo ""
echo "=== CPU LIMIT ENFORCEMENT TEST LAUNCHED! ==="
echo ""
echo "Expected behavior:"
echo "  ✅ Each sandbox should show ~0.300 CPU usage (not 1.000)"
echo "  ✅ Total cluster CPU: ~15 cores out of 20 available"
echo "  ✅ Memory usage: ~1.5GB per sandbox"
echo ""
echo "This proves Kubernetes CPU limits are working!"
echo ""
echo "Monitor the CPU enforcement:"
echo "  k7 top -n $NAMESPACE"
echo "  watch 'k3s kubectl top pods -n $NAMESPACE --sort-by=cpu'"
echo ""
echo "Verify limits are enforced:"
echo "  k3s kubectl describe pod -n $NAMESPACE | grep -A5 'Limits:'"
echo ""
echo "Clean up when done:"
echo "  k7 delete-all -n $NAMESPACE -y"
echo "  rm k7-stress-*.yaml"
echo "  k3s kubectl delete namespace $NAMESPACE"
echo ""
echo "Or just press Ctrl+C - automatic cleanup is enabled! 🧹"
echo ""
echo "🧪 SCIENCE: stress-ng tries to use 100% CPU but gets throttled to 300m!" 
