import ProjectDashboard from './components/ProjectDashboard';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

const theme = createTheme();

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ProjectDashboard />
    </ThemeProvider>
  );
}

export default App;
