import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Home from './pages/Home';
import Settings from './pages/Settings';
import Dashboard from './components/Dashboard';
import EventLog from './components/EventLog';
import LiveFeed from './components/LiveFeed';
import './styles/App.css';

const App: React.FC = () => {
    return (
        <Router>
            <div className="App">
                <Switch>
                    <Route path="/" exact component={Home} />
                    <Route path="/settings" component={Settings} />
                    <Route path="/dashboard" component={Dashboard} />
                    <Route path="/event-log" component={EventLog} />
                    <Route path="/live-feed" component={LiveFeed} />
                </Switch>
            </div>
        </Router>
    );
};

export default App;