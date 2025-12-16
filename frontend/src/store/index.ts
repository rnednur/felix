import { createStore, combineReducers, applyMiddleware, compose } from 'redux'
import { taskMiddleware } from 'react-palm/tasks'
import keplerGlReducer from '@kepler.gl/reducers'

// Combine reducers
const reducers = combineReducers({
  keplerGl: keplerGlReducer,
  // Add other reducers here if needed in the future
})

// Enable Redux DevTools in development
const composeEnhancers =
  (typeof window !== 'undefined' && (window as any).__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) || compose

// Create store with Kepler.gl reducer and react-palm middleware
export const store = createStore(
  reducers,
  {},
  composeEnhancers(applyMiddleware(taskMiddleware))
)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
