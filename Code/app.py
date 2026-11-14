from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from typing import List, Tuple, Optional, Dict
import uuid
import traceback

app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# Store active solver sessions
solver_sessions = {}


class TrialLine:
    """Represents a trial line in the Mikami-Tabuchi algorithm"""
    
    def __init__(self, start: Tuple[int, int], end: Tuple[int, int], 
                 direction: str, level: int, origin: str, parent_point: Optional[Tuple[int, int]] = None):
        self.start = start
        self.end = end
        self.direction = direction
        self.level = level
        self.origin = origin
        self.parent_point = parent_point
        self.base_points = []
    
    def get_points(self) -> List[Tuple[int, int]]:
        """Get all points along the trial line"""
        points = []
        if self.direction == 'horizontal':
            row = self.start[0]
            start_col = min(self.start[1], self.end[1])
            end_col = max(self.start[1], self.end[1])
            for col in range(start_col, end_col + 1):
                points.append((row, col))
        else:
            col = self.start[1]
            start_row = min(self.start[0], self.end[0])
            end_row = max(self.start[0], self.end[0])
            for row in range(start_row, end_row + 1):
                points.append((row, col))
        return points
    
    def contains_point(self, row: int, col: int) -> bool:
        """Check if a point lies on this trial line"""
        if self.direction == 'horizontal':
            return (self.start[0] == row and 
                   col >= min(self.start[1], self.end[1]) and 
                   col <= max(self.start[1], self.end[1]))
        else:
            return (self.start[1] == col and 
                   row >= min(self.start[0], self.end[0]) and 
                   row <= max(self.start[0], self.end[0]))
    
    def to_dict(self) -> Dict:
        """Convert trial line to dictionary for JSON serialization"""
        return {
            'start': list(self.start),
            'end': list(self.end),
            'direction': self.direction,
            'level': self.level,
            'origin': self.origin,
            'parent_point': list(self.parent_point) if self.parent_point else None,
            'base_points': [list(p) for p in self.base_points],
            'points': [list(p) for p in self.get_points()]
        }


class MikamiTabuchiSolver:
    """Mikami-Tabuchi algorithm with bottom-left coordinate system"""
    
    def __init__(self, grid: List[List], start_pos: Tuple[int, int], target_pos: Tuple[int, int]):
        self.grid = grid
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        
        self.source_trial_lines = []
        self.target_trial_lines = []
        self.all_trial_lines = []
        self.current_level = 0
        self.intersection_found = False
        self.intersection_point = None
        self.final_path = []
        self.step_history = []
    
    def is_valid_position(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols
    
    def is_obstacle(self, row: int, col: int) -> bool:
        return self.grid[row][col] == 1
    
    def extend_line(self, start_row: int, start_col: int, direction: str) -> Optional[TrialLine]:
        deltas = {
            'up': (1, 0),      # Up increases row (bottom-left coords)
            'down': (-1, 0),   # Down decreases row
            'left': (0, -1),
            'right': (0, 1)
        }
        
        d_row, d_col = deltas[direction]
        points = []
        current_row, current_col = start_row, start_col
        
        while True:
            next_row = current_row + d_row
            next_col = current_col + d_col
            
            if not self.is_valid_position(next_row, next_col) or self.is_obstacle(next_row, next_col):
                break
            
            current_row, current_col = next_row, next_col
            points.append((current_row, current_col))
        
        if points:
            line_direction = 'vertical' if direction in ['up', 'down'] else 'horizontal'
            return TrialLine(
                (start_row, start_col),
                (current_row, current_col),
                line_direction,
                0,
                None,
                (start_row, start_col)
            )
        return None
    
    def generate_initial_trial_lines(self):
        directions = ['up', 'down', 'left', 'right']
        
        for direction in directions:
            line = self.extend_line(self.start_pos[0], self.start_pos[1], direction)
            if line:
                line.origin = 'source'
                line.level = 0
                self.source_trial_lines.append(line)
                self.all_trial_lines.append(line)
        
        for direction in directions:
            line = self.extend_line(self.target_pos[0], self.target_pos[1], direction)
            if line:
                line.origin = 'target'
                line.level = 0
                self.target_trial_lines.append(line)
                self.all_trial_lines.append(line)
        
        self.current_level = 0
        self.step_history.append({
            'step': 0,
            'action': 'initial_lines',
            'level': 0,
            'message': f'Generated {len(self.source_trial_lines)} source and {len(self.target_trial_lines)} target lines'
        })
    
    def find_line_intersection(self, line1: TrialLine, line2: TrialLine) -> Optional[Tuple[int, int]]:
        if line1.direction == line2.direction:
            return None
        
        h_line = line1 if line1.direction == 'horizontal' else line2
        v_line = line2 if line2.direction == 'vertical' else line1
        
        h_row = h_line.start[0]
        h_start_col = min(h_line.start[1], h_line.end[1])
        h_end_col = max(h_line.start[1], h_line.end[1])
        
        v_col = v_line.start[1]
        v_start_row = min(v_line.start[0], v_line.end[0])
        v_end_row = max(v_line.start[0], v_line.end[0])
        
        if h_start_col <= v_col <= h_end_col and v_start_row <= h_row <= v_end_row:
            return (h_row, v_col)
        
        return None
    
    def check_intersections(self) -> bool:
        for source_line in self.source_trial_lines:
            for target_line in self.target_trial_lines:
                intersection = self.find_line_intersection(source_line, target_line)
                if intersection:
                    self.intersection_point = intersection
                    self.intersection_found = True
                    self.step_history.append({
                        'step': len(self.step_history),
                        'action': 'intersection_found',
                        'level': self.current_level,
                        'message': f'Intersection at {intersection}'
                    })
                    return True
        return False
    
    def generate_next_level_trial_lines(self):
        new_source_lines = []
        new_target_lines = []
        
        for line in [l for l in self.source_trial_lines if l.level == self.current_level]:
            points = line.get_points()
            for point in points:
                line.base_points.append(point)
                perp_direction = 'vertical' if line.direction == 'horizontal' else 'horizontal'
                directions = ['up', 'down'] if perp_direction == 'vertical' else ['left', 'right']
                
                for direction in directions:
                    new_line = self.extend_line(point[0], point[1], direction)
                    if new_line and len(new_line.get_points()) > 1:
                        new_line.origin = 'source'
                        new_line.level = self.current_level + 1
                        new_line.parent_point = point
                        new_source_lines.append(new_line)
                        self.all_trial_lines.append(new_line)
        
        for line in [l for l in self.target_trial_lines if l.level == self.current_level]:
            points = line.get_points()
            for point in points:
                line.base_points.append(point)
                perp_direction = 'vertical' if line.direction == 'horizontal' else 'horizontal'
                directions = ['up', 'down'] if perp_direction == 'vertical' else ['left', 'right']
                
                for direction in directions:
                    new_line = self.extend_line(point[0], point[1], direction)
                    if new_line and len(new_line.get_points()) > 1:
                        new_line.origin = 'target'
                        new_line.level = self.current_level + 1
                        new_line.parent_point = point
                        new_target_lines.append(new_line)
                        self.all_trial_lines.append(new_line)
        
        self.source_trial_lines.extend(new_source_lines)
        self.target_trial_lines.extend(new_target_lines)
        self.current_level += 1
        
        self.step_history.append({
            'step': len(self.step_history),
            'action': 'generate_level',
            'level': self.current_level,
            'message': f'Level {self.current_level}: {len(new_source_lines)} source, {len(new_target_lines)} target'
        })
    
    def backtrace_to_path(self) -> List[Tuple[int, int]]:
        if not self.intersection_point:
            return []
        
        source_line = None
        target_line = None
        
        for line in self.source_trial_lines:
            if line.contains_point(self.intersection_point[0], self.intersection_point[1]):
                source_line = line
                break
        
        for line in self.target_trial_lines:
            if line.contains_point(self.intersection_point[0], self.intersection_point[1]):
                target_line = line
                break
        
        source_to_intersection = []
        current_line = source_line
        
        while current_line and current_line.parent_point:
            source_to_intersection.insert(0, current_line.parent_point)
            parent_found = False
            for line in self.source_trial_lines:
                if (line.contains_point(current_line.parent_point[0], current_line.parent_point[1]) and 
                    line.level == current_line.level - 1):
                    current_line = line
                    parent_found = True
                    break
            if not parent_found:
                break
        
        source_to_intersection.insert(0, self.start_pos)
        source_to_intersection.append(self.intersection_point)
        
        target_to_intersection = []
        current_line = target_line
        
        while current_line and current_line.parent_point:
            target_to_intersection.append(current_line.parent_point)
            parent_found = False
            for line in self.target_trial_lines:
                if (line.contains_point(current_line.parent_point[0], current_line.parent_point[1]) and 
                    line.level == current_line.level - 1):
                    current_line = line
                    parent_found = True
                    break
            if not parent_found:
                break
        
        target_to_intersection.append(self.target_pos)
        self.final_path = source_to_intersection + target_to_intersection[::-1]
        if self.final_path and self.final_path[0] != self.start_pos:
         self.final_path = self.final_path[::-1]
        return self.final_path
    
    def solve(self, max_iterations: int = 50) -> Dict:
        self.generate_initial_trial_lines()
        
        iterations = 0
        while not self.intersection_found and iterations < max_iterations:
            if self.check_intersections():
                self.intersection_found = True
                self.backtrace_to_path()
                break
            
            self.generate_next_level_trial_lines()
            iterations += 1
            
            current_level_source = [l for l in self.source_trial_lines if l.level == self.current_level]
            current_level_target = [l for l in self.target_trial_lines if l.level == self.current_level]
            if not current_level_source and not current_level_target:
                break
        
        return self.get_results()
    
    def get_state_at_level(self, level: int) -> Dict:
        lines_at_level = [l for l in self.all_trial_lines if l.level <= level]
        source_lines = [l for l in lines_at_level if l.origin == 'source']
        target_lines = [l for l in lines_at_level if l.origin == 'target']
        
        return {
            'level': level,
            'trial_lines': [line.to_dict() for line in lines_at_level],
            'source_lines': [line.to_dict() for line in source_lines],
            'target_lines': [line.to_dict() for line in target_lines],
            'source_count': len(source_lines),
            'target_count': len(target_lines)
        }
    
    def get_results(self) -> Dict:
    #"""Return final results with all waypoints and total count"""
     return {
        'success': self.intersection_found,
        'path': [list(p) for p in self.final_path],
        'waypoints': len(self.final_path) if self.final_path else 0,
        'levels_explored': self.current_level + 1,
        'total_trial_lines': len(self.all_trial_lines),
        'intersection_point': list(self.intersection_point) if self.intersection_point else None,
        'all_trial_lines': [line.to_dict() for line in self.all_trial_lines],
        'source_trial_lines': [line.to_dict() for line in self.source_trial_lines],
        'target_trial_lines': [line.to_dict() for line in self.target_trial_lines],
        'step_history': self.step_history,
        'coordinate_system': 'bottom-left'
    }



def parse_grid_input(grid_data: str) -> Tuple[List[List], Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    """Parse grid - convert top-to-bottom input to bottom-to-top coordinates"""
    lines = [line.strip() for line in grid_data.strip().split('\n') if line.strip()]
    grid = []
    start_pos = None
    target_pos = None
    
    # Reverse for bottom-left origin
    for row_idx, line in enumerate(reversed(lines)):
        cells = [cell.strip() for cell in line.split(',')]
        grid_row = []
        
        for col_idx, cell in enumerate(cells):
            if cell.lower() == 's':
                start_pos = (row_idx, col_idx)
                grid_row.append('S')
            elif cell.lower() == 't':
                target_pos = (row_idx, col_idx)
                grid_row.append('T')
            else:
                try:
                    grid_row.append(int(cell))
                except ValueError:
                    grid_row.append(0)
        
        grid.append(grid_row)
    
    return grid, start_pos, target_pos


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        grid_data = data.get('grid_data', '')
        
        if not grid_data:
            return jsonify({'error': 'No grid data provided'}), 400
        
        grid, start_pos, target_pos = parse_grid_input(grid_data)
        
        if not start_pos or not target_pos:
            return jsonify({'error': 'Grid must contain S and T'}), 400
        
        solver = MikamiTabuchiSolver(grid, start_pos, target_pos)
        results = solver.solve()
        
        results['grid'] = grid
        results['grid_size'] = {'rows': len(grid), 'cols': len(grid[0])}
        results['start_pos'] = list(start_pos)
        results['target_pos'] = list(target_pos)
        
        return jsonify(results)
    
    except Exception as e:
        print(f"ERROR in /solve: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/solve/init', methods=['POST'])
def solve_init():
    try:
        data = request.get_json()
        grid_data = data.get('grid_data', '')
        
        if not grid_data:
            return jsonify({'error': 'No grid data'}), 400
        
        grid, start_pos, target_pos = parse_grid_input(grid_data)
        
        if not start_pos or not target_pos:
            return jsonify({'error': 'Grid must contain S and T'}), 400
        
        solver = MikamiTabuchiSolver(grid, start_pos, target_pos)
        solver.generate_initial_trial_lines()
        
        session_id = str(uuid.uuid4())
        solver_sessions[session_id] = solver
        
        print(f"Created session: {session_id}")
        
        return jsonify({
            'session_id': session_id,
            'grid': grid,
            'grid_size': {'rows': len(grid), 'cols': len(grid[0])},
            'start_pos': list(start_pos),
            'target_pos': list(target_pos),
            'current_level': solver.current_level,
            'state': solver.get_state_at_level(0),
            'step_info': solver.step_history[-1] if solver.step_history else {},
            'complete': False,
            'coordinate_system': 'bottom-left'
        })
    
    except Exception as e:
        print(f"ERROR in /solve/init: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/solve/step', methods=['POST'])
def solve_step():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in solver_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        solver = solver_sessions[session_id]
        
        if solver.intersection_found:
            return jsonify({
                'complete': True,
                'success': True,
                'current_level': solver.current_level,
                'state': solver.get_state_at_level(solver.current_level),
                'intersection_point': list(solver.intersection_point),
                'path': [list(p) for p in solver.final_path],
                'step_info': solver.step_history[-1] if solver.step_history else {},
                'message': 'Path found'
            })
        
        if solver.check_intersections():
            solver.backtrace_to_path()
            return jsonify({
                'complete': True,
                'success': True,
                'current_level': solver.current_level,
                'state': solver.get_state_at_level(solver.current_level),
                'intersection_point': list(solver.intersection_point),
                'path': [list(p) for p in solver.final_path],
                'step_info': solver.step_history[-1] if solver.step_history else {},
                'message': f'Intersection at {solver.intersection_point}'
            })
        
        solver.generate_next_level_trial_lines()
        
        current_level_lines = [l for l in solver.all_trial_lines if l.level == solver.current_level]
        if not current_level_lines:
            return jsonify({
                'complete': True,
                'success': False,
                'current_level': solver.current_level,
                'state': solver.get_state_at_level(max(0, solver.current_level - 1)),
                'step_info': solver.step_history[-1] if solver.step_history else {},
                'message': 'No path found'
            })
        
        return jsonify({
            'complete': False,
            'success': False,
            'current_level': solver.current_level,
            'state': solver.get_state_at_level(solver.current_level),
            'step_info': solver.step_history[-1] if solver.step_history else {},
            'message': f'Level {solver.current_level}'
        })
    
    except Exception as e:
        print(f"ERROR in /solve/step: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/solve/cleanup', methods=['POST'])
def solve_cleanup():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id and session_id in solver_sessions:
            del solver_sessions[session_id]
            print(f"Cleaned up session: {session_id}")
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'active_sessions': len(solver_sessions)
    })


if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting Mikami-Tabuchi Flask Server")
    print("="*50)
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*50 + "\n")
    app.run(debug=True, port=5000, host='0.0.0.0')