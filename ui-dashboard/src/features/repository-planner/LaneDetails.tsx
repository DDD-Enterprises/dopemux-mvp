import { Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography } from '@mui/material';

import ConflictPanel from './ConflictPanel';
import ProvenancePanel from './ProvenancePanel';
import type { PlannerLane } from './extensionTypes';

export default function LaneDetails({ lane, onClose }: { lane: PlannerLane | null; onClose: () => void }) {
  return <Dialog open={lane !== null} onClose={onClose} fullWidth maxWidth="md" aria-labelledby="planner-lane-title"><DialogTitle id="planner-lane-title">{lane ? `${lane.projectId} · ${lane.laneId}` : 'Lane details'}</DialogTitle>{lane && <DialogContent><Stack spacing={3}><Typography><strong>Lifecycle state</strong> {lane.lifecycleState}</Typography><ConflictPanel conflicts={lane.conflicts} /><ProvenancePanel lane={lane} /></Stack></DialogContent>}<DialogActions><Button onClick={onClose} aria-label="Close lane details">Close</Button></DialogActions></Dialog>;
}
