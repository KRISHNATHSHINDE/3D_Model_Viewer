const stlPath = "{{ url_for('static', filename='uploads/' + filename) }}";

// Set up the scene, camera, and renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, 600 / 400, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(600, 400);
renderer.setClearColor(0xffffff, 1); // Set background color to white
document.getElementById("stlViewer").appendChild(renderer.domElement);

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const points = [];
const distanceElement = document.getElementById("distance");
const angleElement = document.getElementById("angle");
let measuringDistance = false;
let measuringAngle = false;
let distanceLine = null;
let angleLines = []; // To store lines for angles
let markers = []; // To store point markers

// Add light
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(1, 1, 1).normalize();
scene.add(light);

// Load the STL file
const loader = new THREE.STLLoader();
let mesh;
loader.load(
  stlPath,
  function (geometry) {
    const material = new THREE.MeshPhongMaterial({
      color: 0x555555,
      specular: 0x111111,
      shininess: 0,
    });
    mesh = new THREE.Mesh(geometry, material);
    geometry.computeBoundingBox(); // Ensure bounding box is computed
    geometry.computeBoundingSphere(); // Ensure bounding sphere is computed
    scene.add(mesh);

    // Center the camera on the object
    const middle = new THREE.Vector3();
    geometry.boundingBox.getCenter(middle);
    mesh.geometry.center();
    camera.position.z = middle.length() * 2.5;

    console.log("Mesh added to scene:", mesh);
    console.log("Bounding box:", geometry.boundingBox);
    console.log("Bounding sphere:", geometry.boundingSphere);

    // Render the scene
    function animate() {
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    }
    animate();
  },
  undefined,
  function (error) {
    console.error("Error loading STL file:", error);
  }
);

// Mouse control variables
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };

// Add event listeners for mouse interactions
renderer.domElement.addEventListener("mousedown", (event) => {
  isDragging = true;
  previousMousePosition = {
    x: event.offsetX,
    y: event.offsetY,
  };
});

renderer.domElement.addEventListener("mousemove", (event) => {
  if (isDragging && mesh) {
    const deltaMove = {
      x: event.offsetX - previousMousePosition.x,
      y: event.offsetY - previousMousePosition.y,
    };

    const deltaRotationQuaternion = new THREE.Quaternion().setFromEuler(
      new THREE.Euler(
        toRadians(deltaMove.y * 1),
        toRadians(deltaMove.x * 1),
        0,
        "XYZ"
      )
    );

    mesh.quaternion.multiplyQuaternions(
      deltaRotationQuaternion,
      mesh.quaternion
    );

    previousMousePosition = {
      x: event.offsetX,
      y: event.offsetY,
    };
  }
});

renderer.domElement.addEventListener("mouseup", () => {
  isDragging = false;
});

renderer.domElement.addEventListener("mouseleave", () => {
  isDragging = false;
});

function toRadians(angle) {
  return angle * (Math.PI / 180);
}

// Create sphere to mark points
function createPointMarker(position) {
  const geometry = new THREE.SphereGeometry(0.1, 32, 32);
  const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
  const sphere = new THREE.Mesh(geometry, material);
  sphere.position.copy(position);
  scene.add(sphere);
  markers.push(sphere);
}

// Convert world coordinates to local coordinates of the mesh
function convertWorldToLocal(worldCoords) {
  const localCoords = worldCoords.clone();
  mesh.worldToLocal(localCoords);
  return localCoords;
}

// Offset a point along its normal
function offsetPointAlongNormal(point, normal, offset) {
  const offsetPoint = point.clone();
  offsetPoint.add(normal.clone().multiplyScalar(offset));
  return offsetPoint;
}

// Create line between two points
function createLineBetweenPoints(point1, point2, color = 0x0000ff) {
  const material = new THREE.LineBasicMaterial({ color: color, linewidth: 5 });
  const geometry = new THREE.BufferGeometry().setFromPoints([point1, point2]);
  const line = new THREE.Line(geometry, material);
  mesh.add(line); // Parent the line to the mesh
  return line;
}

// Calculate the angle between three points
function calculateAngle(p1, p2, p3) {
  const v1 = new THREE.Vector3().subVectors(p1, p2).normalize();
  const v2 = new THREE.Vector3().subVectors(p3, p2).normalize();
  const angle = v1.angleTo(v2);
  return THREE.MathUtils.radToDeg(angle); // Convert from radians to degrees
}

// Clear previous measurements
function clearMeasurements() {
  // Remove all angle lines
  angleLines.forEach((line) => mesh.remove(line));
  angleLines.length = 0;

  // Remove the previous distance line
  if (distanceLine) {
    mesh.remove(distanceLine);
    distanceLine = null;
  }

  // Remove all point markers
  markers.forEach((marker) => scene.remove(marker));
  markers.length = 0;
}

// Dimension and angle measurement on click
renderer.domElement.addEventListener("click", (event) => {
  if (!isDragging && mesh && (measuringDistance || measuringAngle)) {
    console.log("Mouse click detected");
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x =
      ((event.clientX - rect.left) / renderer.domElement.clientWidth) * 2 - 1;
    mouse.y =
      -((event.clientY - rect.top) / renderer.domElement.clientHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObject(mesh);

    console.log("Raycaster intersects:", intersects);

    if (intersects.length > 0) {
      console.log("Intersection detected");
      const point = intersects[0].point;
      const normal = intersects[0].face.normal;

      // Offset the point along the normal
      const offsetPoint = offsetPointAlongNormal(point, normal, 0.1);

      points.push(offsetPoint);
      createPointMarker(offsetPoint);

      if (measuringDistance && points.length === 2) {
        clearMeasurements(); // Clear previous measurements

        const distance = points[0].distanceTo(points[1]);
        distanceElement.textContent = distance.toFixed(2) + " units";

        // Convert points to local coordinates
        const localPoint1 = convertWorldToLocal(points[0]);
        const localPoint2 = convertWorldToLocal(points[1]);

        distanceLine = createLineBetweenPoints(localPoint1, localPoint2);
        points.length = 0; // Clear points for next measurement
        measuringDistance = false;
      } else if (measuringAngle && points.length === 3) {
        clearMeasurements(); // Clear previous measurements

        // Convert points to local coordinates
        const localPoint1 = convertWorldToLocal(points[0]);
        const localPoint2 = convertWorldToLocal(points[1]);
        const localPoint3 = convertWorldToLocal(points[2]);

        // Create lines between points
        angleLines.push(createLineBetweenPoints(localPoint1, localPoint2));
        angleLines.push(createLineBetweenPoints(localPoint2, localPoint3));
        angleLines.push(
          createLineBetweenPoints(localPoint3, localPoint1, 0x00ff00)
        );

        const angle = calculateAngle(localPoint1, localPoint2, localPoint3);
        angleElement.textContent = angle.toFixed(2) + " degrees";

        points.length = 0; // Clear points for next measurement
        measuringAngle = false;
      }
    } else {
      console.log("No intersection detected");
    }
  }
});

// Add window resize handling
window.addEventListener("resize", function () {
  const width = 600;
  const height = 400;
  renderer.setSize(width, height);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
});

// Measure button functionality
const measureButton = document.getElementById("measureButton");
measureButton.addEventListener("click", () => {
  measuringDistance = true;
  measuringAngle = false;
  points.length = 0; // Clear previous points
  distanceElement.textContent = ""; // Clear previous distance
  angleElement.textContent = ""; // Clear previous angle
  clearMeasurements(); // Clear any previous measurements
});

// Angle button functionality
const angleButton = document.getElementById("angleButton");
angleButton.addEventListener("click", () => {
  measuringAngle = true;
  measuringDistance = false;
  points.length = 0; // Clear previous points
  distanceElement.textContent = ""; // Clear previous distance
  angleElement.textContent = ""; // Clear previous angle
  clearMeasurements(); // Clear any previous measurements
});
